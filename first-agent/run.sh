#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Virtualenv not found at $ROOT_DIR/.venv"
  echo "Create it first with:"
  echo "  cd $ROOT_DIR"
  echo "  python3 -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  pip install -r requirements.txt"
  exit 1
fi

cd "$ROOT_DIR"
exec "$VENV_PYTHON" -m first_agent.main "$@"
