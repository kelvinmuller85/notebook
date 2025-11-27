#!/bin/bash
set -e

# Note Book Installation Script
# GTK-based sticky notes application with file organization
# Usage: bash install.sh

echo "╔═══════════════════════════════════════════════╗"
echo "║   Note Book Installation                      ║"
echo "║   Sticky Notes & File Organization            ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is not installed. Please install Python 3.7+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Check for GTK3 (system package)
echo "→ Checking for GTK3 system library..."
if ! python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk" 2>/dev/null; then
    echo ""
    echo "⚠ GTK3 Python bindings not found."
    echo "  Install with: sudo apt-get install python3-gi gir1.2-gtk-3.0"
    echo ""
    exit 1
fi
echo "✓ GTK3 and python3-gi detected"
echo ""

# Optional: Install theia-evaluation if needed
if [ ! -d "Files/theia-evaluation" ]; then
    echo "→ Would you like to install theia-evaluation? (y/n)"
    read -r install_theia
    if [ "$install_theia" = "y" ]; then
        echo "→ Installing theia-evaluation..."
        # Theia will need to be downloaded/installed separately
        echo "  See LAUNCHER_README.md for theia-evaluation installation instructions"
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   Installation Complete!                      ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "To launch Note Book:"
echo "  • bash LAUNCH_PROGRAM.sh"
echo ""
echo "Or use the desktop launcher:"
echo "  • Note Book"
echo ""
