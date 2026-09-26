from __future__ import annotations

import os
import signal
from dataclasses import dataclass
from typing import Iterable

import psutil
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Header, Static


@dataclass(frozen=True)
class Connection:
    pid: int
    process: str
    port: int
    protocol: str
    local: str
    remote: str
    status: str


class Porki(App[None]):
    TITLE = "porki"
    SUB_TITLE = "network socket inspector"

    CSS = """
    Screen {
        background: #0f1115;
        color: #abb2bf;
    }

    Header {
        background: #151922;
        color: #61afef;
    }

    DataTable {
        height: 1fr;
        margin: 0 1;
        border: tall #2c323c;
    }

    DataTable > .datatable--header {
        background: #212631;
        color: #61afef;
        text-style: bold;
    }

    DataTable:focus > .datatable--cursor {
        background: #26415c;
        color: #ffffff;
    }

    #guide {
        height: 2;
        padding: 0 1;
        background: #151922;
        color: #7f848e;
    }

    .error {
        color: #e06c75;
    }
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("k", "kill_selected", "Kill", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+x", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.connections: list[Connection] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(id="connections", cursor_type="row", zebra_stripes=True)
        yield Static(
            "  Arrow keys move   r refresh   k terminate selected process   "
            "q / Ctrl+C / Ctrl+X / Ctrl+Q quit",
            id="guide",
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("PID", "PROCESS", "PORT", "PROTO", "LOCAL", "REMOTE", "STATE")
        self.refresh_connections()

    def action_refresh(self) -> None:
        self.refresh_connections()
        self.notify("Sockets refreshed", severity="information")

    def refresh_connections(self) -> None:
        self.connections = list(read_connections())
        self.populate_table()

    def populate_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=False)
        for connection in self.connections:
            table.add_row(
                str(connection.pid),
                connection.process,
                str(connection.port),
                connection.protocol,
                connection.local,
                connection.remote,
                connection.status,
                key=connection_key(connection),
            )

    def action_kill_selected(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count == 0 or table.cursor_row < 0:
            self.notify("No process selected", severity="warning")
            return

        row_key, _ = table.coordinate_to_cell_key((table.cursor_row, 0))
        connection = next(
            (item for item in self.connections if connection_key(item) == row_key.value),
            None,
        )
        if connection is None:
            self.notify("Selected connection no longer exists", severity="warning")
            return
        if connection.pid <= 0:
            self.notify("Kernel socket has no terminable process", severity="warning")
            return
        self.finish_kill(connection)

    def finish_kill(self, connection: Connection) -> None:
        try:
            process = psutil.Process(connection.pid)
            if process.pid == os.getpid():
                self.notify("porki cannot terminate itself", severity="error")
                return
            process.send_signal(signal.SIGTERM)
            self.notify(
                f"SIGTERM sent to {connection.process} ({connection.pid})",
                severity="information",
            )
        except psutil.NoSuchProcess:
            self.notify("Process is no longer running", severity="warning")
        except psutil.AccessDenied:
            self.notify("Access denied, run the app with sudo", severity="error")
        except OSError as error:
            self.notify(f"Termination failed: {error}", severity="error")
        finally:
            self.set_timer(0.4, self.refresh_connections)


def connection_key(connection: Connection) -> str:
    return f"{connection.pid}:{connection.protocol}:{connection.local}:{connection.remote}"


def format_address(address) -> str:
    if not address:
        return "-"
    host, port = address[:2]
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def process_name(pid: int) -> str:
    try:
        return psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "?"


def read_connections() -> Iterable[Connection]:
    try:
        sockets = psutil.net_connections(kind="inet")
    except psutil.AccessDenied:
        return []

    connections = []
    for socket in sockets:
        if not socket.laddr:
            continue
        local = format_address(socket.laddr)
        remote = format_address(socket.raddr)
        port = socket.laddr.port
        protocol = "TCP" if socket.type == 1 else "UDP"
        status = socket.status if protocol == "TCP" else "UNCONN"
        connections.append(
            Connection(
                pid=socket.pid or 0,
                process=process_name(socket.pid) if socket.pid else "kernel",
                port=port,
                protocol=protocol,
                local=local,
                remote=remote,
                status=status,
            )
        )
    return sorted(
        connections,
        key=lambda item: (item.port, item.protocol, item.pid, item.remote),
    )


if __name__ == "__main__":
    Porki().run()


def main() -> None:
    Porki().run()
