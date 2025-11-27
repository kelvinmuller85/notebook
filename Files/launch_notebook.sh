#!/bin/bash

# Get the directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_DIR="/home/${USER}/.local/share/notebook"

# Set Python path to include the Files directory
export PYTHONPATH="${APP_DIR}/Files:${PYTHONPATH}"

# Set GI typelib path if needed
export GI_TYPELIB_PATH="/usr/lib/girepository-1.0:${GI_TYPELIB_PATH}"

# If running in virtual environment, activate it
VENV="${APP_DIR}/venv"
if [ -d "$VENV" ]; then
    source "${VENV}/bin/activate"
fi

# Run the application with the new directory structure
exec python3 "${APP_DIR}/Files/src/notebook_wrapper.py" "$@"