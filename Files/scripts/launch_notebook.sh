#!/bin/bash
# Launcher for Note Book

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Clear Python cache to ensure latest code is loaded
rm -rf "$SCRIPT_DIR/__pycache__"

# Launch the Note Book wrapper (proper GUI with file organization)
if [ -f "notebook_wrapper.py" ]; then
    exec python3 -B notebook_wrapper.py
else
    echo "Note Book application files not found in $SCRIPT_DIR"
    exit 1
fi
