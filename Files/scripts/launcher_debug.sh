#!/bin/bash
# Set environment
NOTEBOOK_DIR="$HOME/.local/share/notebook/Files"
WRAPPER_PATH="$NOTEBOOK_DIR/notebook_wrapper.py"
export PYTHONPATH="$NOTEBOOK_DIR${PYTHONPATH:+:$PYTHONPATH}"
export GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0"
export XDG_DATA_DIRS="/usr/local/share:/usr/share${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"

# For debugging
echo "=== Notebook Launcher Debug ==="
echo "PYTHONPATH: $PYTHONPATH"
echo "Current directory: $PWD"
echo "Python version: $(python3 --version)"
echo "========================="

# Use system Python with GTK bindings
if [ -f "$WRAPPER_PATH" ]; then
    cd "$NOTEBOOK_DIR"
    exec python3 "$WRAPPER_PATH" "$@"
else
    echo "Error: notebook_wrapper.py not found in $NOTEBOOK_DIR"
    exit 1
fi