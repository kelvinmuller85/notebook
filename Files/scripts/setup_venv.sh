#!/bin/bash
set -euo pipefail

VENV_DIR="$HOME/.local/share/notebook_venv"
LOG_FILE="$HOME/.local/share/notebook/logs/venv_setup.log"

mkdir -p "$(dirname "$LOG_FILE")"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "=== Setting up Python Environment $(date) ==="

# Create virtual environment
python3 -m venv "$VENV_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install required packages
pip install PyGObject

# Verify GTK installation
python3 -c "
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3')
from gi.repository import Gtk, GtkSource
print('GTK environment verified successfully')
"

echo "=== Setup Complete $(date) ==="