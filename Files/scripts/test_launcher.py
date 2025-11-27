#!/usr/bin/env python3
import sys
import os
import traceback

def setup_environment():
    """Set up the environment variables"""
    notebook_dir = os.path.join(os.path.expanduser('~'), '.local/share/notebook/Files')
    os.environ['PYTHONPATH'] = notebook_dir
    os.environ['GI_TYPELIB_PATH'] = '/usr/lib/x86_64-linux-gnu/girepository-1.0'
    os.environ['XDG_DATA_DIRS'] = '/usr/local/share:/usr/share:' + os.environ.get('XDG_DATA_DIRS', '')
    sys.path.insert(0, notebook_dir)

def test_imports():
    """Test all required imports"""
    try:
        print("Testing GTK imports...")
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('GtkSource', '4')
        from gi.repository import Gtk, GtkSource
        print("GTK imports successful")
        return True
    except Exception as e:
        print("Error importing GTK:", str(e))
        print("Traceback:")
        traceback.print_exc()
        return False

def check_files():
    """Check if all required files exist"""
    required_files = [
        '~/.local/share/notebook/Files/notebook_wrapper.py',
        '~/.local/bin/notebook-launcher',
        '~/.local/share/applications/notebook.desktop'
    ]
    
    all_exist = True
    print("\nChecking required files:")
    for file_path in required_files:
        expanded_path = os.path.expanduser(file_path)
        exists = os.path.exists(expanded_path)
        print(f"{file_path}: {'EXISTS' if exists else 'MISSING'}")
        if exists:
            print(f"  Permissions: {oct(os.stat(expanded_path).st_mode)[-3:]}")
        all_exist = all_exist and exists
    return all_exist

def main():
    print("=== Note Book Diagnostic Test ===")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    setup_environment()
    print("\nEnvironment variables:")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"GI_TYPELIB_PATH: {os.environ.get('GI_TYPELIB_PATH', 'Not set')}")
    print(f"XDG_DATA_DIRS: {os.environ.get('XDG_DATA_DIRS', 'Not set')}")
    
    imports_ok = test_imports()
    files_ok = check_files()
    
    if imports_ok and files_ok:
        print("\nAll tests passed! Attempting to launch notebook_wrapper.py...")
        wrapper_path = os.path.expanduser('~/.local/share/notebook/Files/notebook_wrapper.py')
        os.chdir(os.path.dirname(wrapper_path))
        exec(open(wrapper_path).read())
    else:
        print("\nTests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()