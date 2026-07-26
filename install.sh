#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ -x "$ROOT_DIR/.photo_tool_env/bin/python" ]; then
  PYTHON_BIN="$ROOT_DIR/.photo_tool_env/bin/python"
  VENV_BIN_DIR="$ROOT_DIR/.photo_tool_env/bin"
else
  PYTHON_BIN="$(command -v python3 || command -v python)"
  VENV_BIN_DIR=""
fi

export PIPX_HOME="${PIPX_HOME:-$HOME/.local/pipx}"
export PIPX_BIN_DIR="${PIPX_BIN_DIR:-$HOME/.local/bin}"
mkdir -p "$PIPX_HOME" "$PIPX_BIN_DIR"

if [ -n "$VENV_BIN_DIR" ] && [ -x "$VENV_BIN_DIR/pipx" ]; then
  PIPX_BIN="$VENV_BIN_DIR/pipx"
elif [ -n "$VENV_BIN_DIR" ]; then
  echo "Installing pipx into the existing virtual environment..."
  "$PYTHON_BIN" -m pip install pipx
  PIPX_BIN="$VENV_BIN_DIR/pipx"
else
  if ! command -v pipx >/dev/null 2>&1; then
    echo "Installing pipx with the user site Python..."
    "$PYTHON_BIN" -m pip install --user pipx
  fi
  PIPX_BIN="$(command -v pipx)"
fi

export PATH="$PIPX_BIN_DIR:$HOME/.local/bin:$PATH"
if [ -n "$VENV_BIN_DIR" ]; then
  export PATH="$VENV_BIN_DIR:$PATH"
fi

if [ -n "$HOME" ]; then
  SHELL_RC=""
  for candidate in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
    if [ -f "$candidate" ]; then
      SHELL_RC="$candidate"
      break
    fi
  done

  if [ -n "$SHELL_RC" ]; then
    grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_RC" 2>/dev/null || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
  fi
fi

if ! command -v "$PIPX_BIN" >/dev/null 2>&1; then
  echo "pipx could not be found after installation." >&2
  exit 1
fi

echo "Installing photo-tools with pipx..."
"$PIPX_BIN" install --force --python "$PYTHON_BIN" .

hash -r 2>/dev/null || true

if [ -x "$PIPX_BIN_DIR/photo-add-image" ]; then
  echo "Installed executable: $PIPX_BIN_DIR/photo-add-image"
  "$PIPX_BIN_DIR/photo-add-image" --help | head -10
else
  echo "Expected executable was not created at $PIPX_BIN_DIR/photo-add-image" >&2
  exit 1
fi
