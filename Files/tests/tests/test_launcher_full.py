#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
import time
import shutil
from pathlib import Path

# Set up logging
log_dir = Path.home() / '.local/share/notebook/logs'
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'launcher_test.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

def check_file_exists(path, desc):
    """Check if a file exists and log its status"""
    path = Path(path).expanduser()
    exists = path.exists()
    logging.info(f"Checking {desc} at {path}: {'EXISTS' if exists else 'MISSING'}")
    if exists:
        logging.debug(f"File permissions: {oct(path.stat().st_mode)[-3:]}")
        if path.is_symlink():
            logging.debug(f"Symlink points to: {path.resolve()}")
    return exists

def verify_python_imports():
    """Verify Python environment and required imports"""
    logging.info("Testing Python imports...")
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('GtkSource', '3')
        from gi.repository import Gtk, GtkSource
        logging.info("Python GTK imports successful")
        return True
    except Exception as e:
        logging.error(f"Python import error: {str(e)}")
        return False

def fix_permissions():
    """Fix permissions on critical files"""
    files_to_fix = [
        ('~/.local/bin/notebook-launcher', 0o755),
        ('~/.local/share/applications/notebook.desktop', 0o644)
    ]
    
    for file_path, mode in files_to_fix:
        path = Path(file_path).expanduser()
        if path.exists():
            try:
                path.chmod(mode)
                logging.info(f"Fixed permissions for {path}")
            except Exception as e:
                logging.error(f"Failed to fix permissions for {path}: {e}")

def verify_installation():
    """Verify all required components are installed"""
    checks = [
        ('~/.local/share/notebook/Files', 'Application files directory'),
        ('~/.local/bin/notebook-launcher', 'Launcher script'),
        ('~/.local/share/applications/notebook.desktop', 'Desktop entry'),
        ('~/.local/share/notebook_venv', 'Python virtual environment'),
    ]
    
    all_exist = True
    for path, desc in checks:
        if not check_file_exists(path, desc):
            all_exist = False
            
    return all_exist

def fix_desktop_file():
    """Ensure desktop file is correctly configured"""
    desktop_file = Path('~/.local/share/applications/notebook.desktop').expanduser()
    content = '''[Desktop Entry]
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
'''
    try:
        desktop_file.write_text(content)
        desktop_file.chmod(0o644)
        logging.info("Desktop file created/updated successfully")
        subprocess.run(['update-desktop-database', str(desktop_file.parent)], check=False)
    except Exception as e:
        logging.error(f"Failed to update desktop file: {e}")

def copy_required_files():
    """Copy required files from source to installation directory"""
    source_dir = Path('/home/jolly/Desktop/Note Book')
    files_dir = Path('~/.local/share/notebook/Files').expanduser()
    
    try:
        if not files_dir.exists():
            files_dir.mkdir(parents=True)
        
        # Copy Files directory contents
        if (source_dir / 'Files').exists():
            for file in (source_dir / 'Files').glob('*'):
                dest = files_dir / file.name
                if file.is_file():
                    shutil.copy2(file, dest)
                else:
                    shutil.copytree(file, dest, dirs_exist_ok=True)
            logging.info("Copied application files successfully")
        else:
            logging.error("Source Files directory not found")
            return False
            
        return True
    except Exception as e:
        logging.error(f"Failed to copy files: {e}")
        return False

def test_launcher():
    """Test if the launcher actually starts the program"""
    try:
        logging.info("Testing launcher execution...")
        process = subprocess.Popen(['notebook-launcher'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a bit to see if the process stays running
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            logging.info("Launcher successfully started and program is running")
            process.terminate()  # Clean up
            return True
        else:
            stdout, stderr = process.communicate()
            logging.error(f"Launcher failed to keep running")
            logging.error(f"stdout: {stdout.decode()}")
            logging.error(f"stderr: {stderr.decode()}")
            return False
    except Exception as e:
        logging.error(f"Error testing launcher: {e}")
        return False

def main():
    logging.info("=== Starting Launcher Test ===")
    
    # Step 1: Verify installation
    if not verify_installation():
        logging.info("Installation incomplete, fixing...")
        copy_required_files()
    
    # Step 2: Fix permissions
    fix_permissions()
    
    # Step 3: Update desktop file
    fix_desktop_file()
    
    # Step 4: Verify Python imports
    if not verify_python_imports():
        logging.error("Python environment verification failed")
        return False
    
    # Step 5: Test launcher
    success = test_launcher()
    
    logging.info("=== Test Complete ===")
    logging.info(f"Final Result: {'SUCCESS' if success else 'FAILURE'}")
    
    # Copy log to main directory for visibility
    try:
        shutil.copy2(log_file, '/home/jolly/Desktop/Note Book/LAUNCHER_TEST_REPORT.log')
    except Exception as e:
        logging.error(f"Failed to copy log file: {e}")
    
    return success

if __name__ == '__main__':
    sys.exit(0 if main() else 1)