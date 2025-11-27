# Note Book

A GTK-based sticky notes application with integrated file organization and optional web-based code editing through Theia IDE evaluation.

## Features

- **Sticky Notes**: Quick note taking with persistent storage
- **File Organization**: Organize notes by projects and categories
- **Optional Theia IDE Integration**: Web-based code editing (install via github-install.sh)
- **Progress Tracking**: Track progress notes and milestones
- **GTK3 UI**: Native Linux desktop interface

## Quick Start

### System Requirements

Install GTK3 and Python bindings:

```bash
sudo apt-get install python3-gi gir1.2-gtk-3.0
```

### Automatic Installation (Recommended)

```bash
bash install.sh
```

This will:
1. Verify Python 3 and GTK3 are installed
2. Verify all dependencies
3. Display launch instructions

### Manual Installation

If you prefer manual setup:

```bash
# Verify system packages
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk"
```

## Running Note Book

### Using the Launcher Script
```bash
bash LAUNCH_PROGRAM.sh
```

### Using Desktop Launcher
Click the **Note Book** application in your application menu.

### Direct Python
```bash
cd Files
python3 manager.py
```

## Requirements

### System Packages
- python3-gi
- gir1.2-gtk-3.0
- libgtk-3-0

### Python
- Python 3.7+
- GTK3 (system library)

## Optional: Theia IDE Integration

Theia Evaluation provides a web-based code editor interface. To install:

```bash
bash github-install.sh
```

This script will:
1. Check for existing Theia installation
2. Prompt user to install theia-evaluation
3. Set up the optional component for web-based code editing

**Note**: Theia is completely optional. Note Book works perfectly fine without it.

## Project Structure

```
Note Book/
├── LAUNCH_PROGRAM.sh           # Main launcher
├── install.sh                  # Installation script
├── github-install.sh           # GitHub optional components installer
├── Files/
│   ├── manager.py              # Main application
│   ├── note_extended.py        # Note extension module
│   └── notes/                  # Stored notes
├── Progress Notes/             # Progress tracking
└── README.md                   # This file
```

## Usage Tips

1. **Creating Notes**: Use the GUI to create new sticky notes
2. **Organizing**: Drag notes into categories
3. **Searching**: Use the search feature to find notes quickly
4. **Backing Up**: Notes are stored in `Files/notes/` directory
5. **Web Editing**: After running github-install.sh, use Theia for editing code or complex notes

## Troubleshooting

### GUI Won't Launch
Verify GTK3 is installed:
```bash
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('GTK3 OK')"
```

### Import Errors
Re-run `bash install.sh` to verify all dependencies.

### Theia Not Available
If you want web-based code editing, run:
```bash
bash github-install.sh
```

### Display Issues
If running over SSH, ensure X11 forwarding is enabled:
```bash
ssh -X user@host
```

## Performance Notes

- Application is lightweight for note-taking
- Theia IDE (if installed) can be memory-intensive (requires significant RAM)
- Theia is optional and does not impact core Note Book functionality

## License

This project is part of the Magi suite of tools.

## Author

Terry Carry (terrycarry32)
