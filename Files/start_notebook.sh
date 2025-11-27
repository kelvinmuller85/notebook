#!/bin/bash
set -euo pipefail

# Get script directory
APP_DIR="$(cd "$(dirname "$0")" && pwd)"

# Set initial PYTHONPATH
export PYTHONPATH="$APP_DIR"

# GObject introspection uses system python-gi, not venv
# We'll use system Python for the main app (for PyGObject/GTK support)

# Set GI typelib path if needed
export GI_TYPELIB_PATH="/usr/lib/girepository-1.0:${GI_TYPELIB_PATH:-}"

# Update PYTHONPATH with additional paths
export PYTHONPATH="$APP_DIR:$APP_DIR/src:${PYTHONPATH}"

# Launch the app using system python3 (has PyGObject)
cd "$APP_DIR"
exec /usr/bin/python3 "$APP_DIR/src/notebook_wrapper.py"
