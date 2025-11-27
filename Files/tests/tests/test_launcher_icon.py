#!/usr/bin/python3
"""
Test that the desktop launcher icon actually works.
Simulates clicking the icon and verifies GUI opens.
"""

import subprocess
import time
import sys
import os

def test_launcher_opens_gui():
    """Test that launcher script opens the GUI"""
    print("Testing launcher icon...")
    
    # Path to launcher script
    launcher = "/home/copsn/Desktop/Note Book/Files/launch_notebook.sh"
    
    if not os.path.exists(launcher):
        print(f"✗ FAILED: Launcher not found at {launcher}")
        return False
    
    # Check if it's executable
    if not os.access(launcher, os.X_OK):
        print(f"✗ FAILED: Launcher not executable")
        return False
    
    print(f"  Launching: {launcher}")
    
    # Start the launcher
    try:
        proc = subprocess.Popen(
            [launcher],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(launcher)
        )
        
        # Wait 2 seconds for GUI to open
        time.sleep(2)
        
        # Check if process is still running (GUI should be up)
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            print(f"✗ FAILED: Process exited immediately")
            print(f"  stdout: {stdout.decode()}")
            print(f"  stderr: {stderr.decode()}")
            return False
        
        # Check for visible windows
        result = subprocess.run(
            ["wmctrl", "-l"],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        windows = result.stdout
        if "Note Book" in windows or "Note" in windows:
            print(f"✓ GUI opened successfully")
            print(f"  Windows found: {[line for line in windows.split('\\n') if 'Note' in line]}")
            
            # Kill the process
            proc.terminate()
            proc.wait(timeout=2)
            return True
        else:
            print(f"✗ FAILED: No GUI windows found")
            print(f"  Windows: {windows}")
            proc.terminate()
            proc.wait(timeout=2)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ FAILED: Timeout waiting for GUI")
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            proc.kill()
        return False
    except FileNotFoundError:
        print(f"✗ FAILED: wmctrl not found (install with: sudo apt install wmctrl)")
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            proc.kill()
        return False
    except Exception as e:
        print(f"✗ FAILED: {e}")
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            proc.kill()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("LAUNCHER ICON TEST")
    print("=" * 60)
    
    if test_launcher_opens_gui():
        print("\n✓ Launcher icon works!")
        sys.exit(0)
    else:
        print("\n✗ Launcher icon FAILED!")
        sys.exit(1)
