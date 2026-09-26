#!/bin/sh
set -eu

INSTALL_DIR="${PORKI_INSTALL_DIR:-$HOME/.local/share/porki}"
COMMAND_PATH="$HOME/.local/bin/porki"

rm -f "$COMMAND_PATH"
rm -rf "$INSTALL_DIR"

printf '%s\n' "porki has been uninstalled."
