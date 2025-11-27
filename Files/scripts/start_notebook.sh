#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

# Kill any existing sticky instance
pkill -f sticky_unmodified.py 2>/dev/null || true

# Wait a moment
sleep 0.5

# Launch Sticky Notes with proper styling from src directory using system Python
# (Note Book requires system-provided gi/gtk3 bindings which are not pip-installable in venv)
cd "$APP_DIR/src"
exec python3 sticky_unmodified.py
