#!/bin/bash
set -euo pipefail

# System requirements
echo "=== Installing System Requirements ==="
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-gtksource-3.0 \
    gir1.2-gtksource-4 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    gobject-introspection

# Setup directories
echo "=== Setting up Directories ==="
mkdir -p ~/.local/share/notebook/{Files,logs} ~/.local/bin ~/.local/share/applications

# Copy application files
echo "=== Copying Application Files ==="
cp -r "/home/jolly/Desktop/Note Book/Files/"* ~/.local/share/notebook/Files/

# Create and configure virtual environment
echo "=== Setting up Python Environment ==="
python3 -m venv ~/.local/share/notebook_venv
source ~/.local/share/notebook_venv/bin/activate
pip install PyGObject

# Create launcher
echo "=== Creating Launcher ==="
cat > ~/.local/bin/notebook-launcher << 'EOF'
#!/bin/bash
# Set environment
NOTEBOOK_DIR="$HOME/.local/share/notebook/Files"
export PYTHONPATH="$NOTEBOOK_DIR:${PYTHONPATH:-}"
export GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0"
export XDG_DATA_DIRS="/usr/local/share:/usr/share:${XDG_DATA_DIRS:-}"

# Use system Python with GTK bindings
if [ -f "$NOTEBOOK_DIR/notebook_wrapper.py" ]; then
    cd "$NOTEBOOK_DIR"
    exec python3 -c "
import os, sys
sys.path.insert(0, os.environ['PYTHONPATH'])
with open('notebook_wrapper.py') as f:
    exec(f.read())
" "$@"
else
    echo "Error: notebook_wrapper.py not found in $NOTEBOOK_DIR"
    exit 1
fi
EOF
chmod +x ~/.local/bin/notebook-launcher

# Create desktop entry
echo "=== Creating Desktop Entry ==="
cat > ~/.local/share/applications/notebook.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Note Book
Comment=Sticky Notes with Code Support
Exec=notebook-launcher
Icon=text-editor
Terminal=false
Categories=Utility;TextEditor;Development;
Keywords=notes;sticky;code;
StartupNotify=true
StartupWMClass=notebook
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications

echo "=== Setup Complete ==="
echo "Testing launcher..."
notebook-launcher --version