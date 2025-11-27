#!/bin/bash
set -euo pipefail

# Launch script for Note Book - Handles both direct and proot execution
# Detects whether system has required libraries or needs proot environment

# Paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOTFS_DIR="$HOME/.local/share/notebook_rootfs"
VENV_DIR="$HOME/.local/share/notebook_venv"
APP_DIR="$HOME/.local/share/notebook_app"
LOG_FILE="$HOME/.local/share/notebook/launch.log"

mkdir -p "$(dirname "$LOG_FILE")"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "=== Note Book Launch $(date) ==="

# Check if virtualenv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Please run the installer first."
    echo "Double-click notebook.desktop in the main folder to install."
    exit 1
fi

# Function to check if system has required GTK/GI packages
check_system_libs() {
    python3 -c "
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3')
from gi.repository import Gtk, GtkSource
" 2>/dev/null
}

# First try direct execution with system libraries
if check_system_libs; then
    echo "System libraries available, launching directly..."
    source "$VENV_DIR/bin/activate"
    exec python "$APP_DIR/Files/notebook_wrapper.py"
fi

# Fallback to proot if system libraries aren't sufficient
echo "System libraries not found, using proot environment..."

# Check for proot binary
PROOT="$SCRIPT_DIR/usb-installer/proot"
if [ ! -x "$PROOT" ]; then
    PROOT=$(command -v proot || true)
    if [ -z "$PROOT" ]; then
        echo "Error: proot not found. Please install proot or run the installer again."
        exit 1
    fi
fi

# Check for rootfs
if [ ! -d "$ROOTFS_DIR" ] || [ ! -f "$ROOTFS_DIR/.installed_marker" ]; then
    echo "Error: rootfs not found. Please run the installer first."
    exit 1
fi

# Set up X11 environment
XAUTH_FILE=$(mktemp /tmp/notebook-xauth.XXXXXX)
touch "$XAUTH_FILE"
xauth nlist "$DISPLAY" | sed -e 's/^..../ffff/' | xauth -f "$XAUTH_FILE" nmerge -

# Launch via proot with display access
exec "$PROOT" -r "$ROOTFS_DIR" \
    -b /dev -b /proc -b /sys \
    -b /tmp/.X11-unix:/tmp/.X11-unix \
    -b "$XAUTH_FILE:/root/.Xauthority" \
    -b "$HOME:$HOME" \
    /bin/bash -c "
        source $VENV_DIR/bin/activate
        export DISPLAY=$DISPLAY
        cd $HOME
        exec python $APP_DIR/Files/notebook_wrapper.py
    "