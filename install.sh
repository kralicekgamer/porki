#!/bin/sh
set -eu

REPO_URL="${PORKI_REPO_URL:-https://github.com/kralicekgamer/porki.git}"
INSTALL_DIR="${PORKI_INSTALL_DIR:-$HOME/.local/share/porki}"
REPO_DIR="$INSTALL_DIR/repo"
BIN_DIR="$HOME/.local/bin"
COMMAND_PATH="$BIN_DIR/porki"

printf '%s\n' "Installing porki..."

if [ -d "$REPO_DIR/.git" ]; then
    git -C "$REPO_DIR" pull --ff-only
elif [ -e "$REPO_DIR" ]; then
    printf '%s\n' "Error: $REPO_DIR exists but is not a Git repository." >&2
    exit 1
else
    mkdir -p "$INSTALL_DIR"
    git clone --depth 1 "$REPO_URL" "$REPO_DIR"
fi

command -v python3 >/dev/null 2>&1 || {
    printf '%s\n' "Error: python3 is required." >&2
    exit 1
}

python3 -m venv "$REPO_DIR/.venv"
"$REPO_DIR/.venv/bin/python" -m pip install --requirement "$REPO_DIR/requirements.txt"

mkdir -p "$BIN_DIR"
printf '%s\n' '#!/bin/sh' "exec \"$REPO_DIR/.venv/bin/python\" \"$REPO_DIR/porki.py\" \"\$@\"" > "$COMMAND_PATH"
chmod +x "$COMMAND_PATH"

printf '\n%s\n' "Installation complete."
printf '%s\n' "Run: porki"
case ":${PATH}:" in
    *":$BIN_DIR:"*) ;;
    *) printf '%s\n' "Add $BIN_DIR to PATH if the command is not found." ;;
esac
