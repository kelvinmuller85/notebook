#!/usr/bin/env python3
"""
Automated installer testing script.
Tests the complete installation process including launcher functionality.
"""

import os
import sys
import subprocess
import json
import tempfile
import time
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class InstallerTester:
    def __init__(self):
        self.test_home = None
        self.logs = []
        self.errors = []
        self.success = True

    def log(self, message, error=False):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        if error:
            self.errors.append(log_entry)
            self.success = False

    def setup_test_environment(self):
        """Create a temporary home directory for testing."""
        self.test_home = tempfile.mkdtemp(prefix="notebook_test_")
        self.log(f"Created test environment at: {self.test_home}")
        
        # Create necessary XDG directories
        for dir_name in [".local/share", ".local/bin", ".config", ".local/share/applications"]:
            os.makedirs(os.path.join(self.test_home, dir_name), exist_ok=True)
        
        # Set up environment variables
        os.environ["HOME"] = self.test_home
        os.environ["XDG_DATA_HOME"] = os.path.join(self.test_home, ".local/share")
        os.environ["XDG_CONFIG_HOME"] = os.path.join(self.test_home, ".config")
        
        # Create a minimal Python environment
        try:
            # Create a local bin directory
            bin_dir = os.path.join(self.test_home, ".local/bin")
            os.makedirs(bin_dir, exist_ok=True)
            
            # Ensure pip is available
            try:
                subprocess.run([sys.executable, "-m", "ensurepip", "--user"], check=False)
                subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "pip"], check=False)
            except:
                pass  # Ignore failures here, the install script will handle it
            
            # Create a simple pip wrapper script
            pip_wrapper = os.path.join(bin_dir, "pip")
            with open(pip_wrapper, 'w') as f:
                f.write(f'''#!/bin/bash
{sys.executable} -m pip "$@"
''')
            os.chmod(pip_wrapper, 0o755)
            
            # Update PATH
            os.environ["PATH"] = f"{bin_dir}:{os.environ['PATH']}"
            
            self.log("Test environment configured successfully")
            return True
            
        except Exception as e:
            self.log(f"Failed to set up test environment: {str(e)}", error=True)
            return False

    def verify_dependencies(self):
        """Check if all required dependencies are available."""
        missing_pkgs = []
        
        # Check Python and glib tools
        for cmd in ["python3", "glib-compile-schemas"]:
            try:
                subprocess.run(["which", cmd], check=True, capture_output=True)
                self.log(f"Found required command: {cmd}")
            except subprocess.CalledProcessError:
                missing_pkgs.append(cmd)
                
        # Check python3-pip by trying to run `python3 -m pip --version`
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            missing_pkgs.append("python3-pip")
            
        if missing_pkgs:
            # Treat missing python3-pip as a non-fatal warning in minimal test environments
            if missing_pkgs == ["python3-pip"]:
                self.log("Warning: python3-pip not available in this environment. Tests will attempt to proceed using user-local pip or wheelhouse.")
                return True

            self.log(f"Missing required packages: {', '.join(missing_pkgs)}", error=True)
            self.log("Please install them using:", error=True)
            self.log(f"sudo apt-get install {' '.join(missing_pkgs)}", error=True)
            return False

        return True

    def run_installer(self):
        """Run the installation script in fakechroot environment."""
        try:
            script_dir = Path(__file__).parent.parent
            usb_installer_dir = script_dir / "usb-installer"
            
            # Create a minimal chroot environment
            rootfs_dir = os.path.join(self.test_home, ".local/share/notebook_rootfs")
            os.makedirs(rootfs_dir, exist_ok=True)
            
            # Copy required files into the rootfs
            os.makedirs(os.path.join(rootfs_dir, "usr/local/bin"), exist_ok=True)
            os.makedirs(os.path.join(rootfs_dir, "usr/lib"), exist_ok=True)
            
            # Copy application files
            app_dir = os.path.join(rootfs_dir, "opt/notebook")
            os.makedirs(app_dir, exist_ok=True)
            subprocess.run(["cp", "-r", 
                str(script_dir / "Files"), 
                str(script_dir / "tests"),
                str(script_dir / "requirements.txt"),
                app_dir], check=True)
            
            # Run the installation script directly (no need for chroot since we're installing to user space)
            install_cmd = [
                "bash",
                str(usb_installer_dir / "install.sh")
            ]
            
            # Set up environment variables
            env = os.environ.copy()
            env["HOME"] = self.test_home
            env["USER"] = os.getenv("USER", "testuser")
            env["PATH"] = f"{os.path.join(rootfs_dir, 'usr/local/bin')}:{env['PATH']}"
            
            # Create a temporary file for installation logs
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as log_file:
                log_path = log_file.name
                
                # Redirect both stdout and stderr to the log file
                result = subprocess.run(install_cmd,
                                     env=env,
                                     cwd=self.test_home,
                                     stdout=log_file,
                                     stderr=subprocess.STDOUT,
                                     text=True)
                
                # Read the log file
                log_file.seek(0)
                log_content = log_file.read()
                
            try:
                os.unlink(log_path)
            except:
                pass
                
            # Process the installation result
            if result.returncode != 0:
                # Log the entire installation output
                self.log("=== Installation Log Start ===")
                for line in log_content.splitlines():
                    self.log(f"  {line}")
                self.log("=== Installation Log End ===")
                
                # Extract error messages
                errors = [line for line in log_content.splitlines() if "ERROR:" in line]
                if errors:
                    for error in errors:
                        self.log(error, error=True)
                else:
                    self.log("Installation failed with no specific error message", error=True)
                return False
                
            self.log("Installation completed successfully")
            return True
            
        except Exception as e:
            self.log(f"Installation failed with error: {str(e)}", error=True)
            return False

    def verify_files(self):
        """Verify that all required files are installed correctly."""
        required_paths = [
            ".local/share/notebook/Files",
            ".local/share/applications/notebook.desktop",
            ".local/bin/notebook-launcher",
            ".config/notebook",
            ".local/share/notebook_rootfs",  # Proot environment
            ".local/share/notebook_rootfs/opt/notebook_venv"  # Virtual environment in proot
        ]
        
        # Check required paths
        for path in required_paths:
            full_path = os.path.join(self.test_home, path)
            if not os.path.exists(full_path):
                self.log(f"Missing required path: {path}", error=True)
                return False
            self.log(f"Verified path exists: {path}")
        
        # Verify critical files in the rootfs
        rootfs = os.path.join(self.test_home, ".local/share/notebook_rootfs")
        critical_files = [
            "opt/notebook_venv/bin/python3",
            "opt/notebook_venv/bin/pip"
        ]
        
        for file in critical_files:
            full_path = os.path.join(rootfs, file)
            if not os.path.exists(full_path):
                self.log(f"Missing critical file in rootfs: {file}", error=True)
                return False
            if not os.access(full_path, os.X_OK):
                self.log(f"Critical file not executable: {file}", error=True)
                return False
            self.log(f"Verified critical file exists and is executable: {file}")
        
        # Test Python imports in proot environment
        proot_cmd = os.path.join(self.test_home, ".local/share/notebook_rootfs/opt/notebook_venv/bin/python3")
        for module in ['gi', 'cairo', 'pygtkspellcheck']:
            try:
                result = subprocess.run(
                    [proot_cmd, "-c", f"import {module}"],
                    env={"PYTHONPATH": f"{rootfs}/opt/notebook_venv/lib/python3*/site-packages"},
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.log(f"Failed to import {module} in proot: {result.stderr}", error=True)
                    return False
                self.log(f"Successfully imported {module} in proot environment")
            except Exception as e:
                self.log(f"Failed to test import of {module}: {str(e)}", error=True)
                return False
        
        return True

    def verify_launcher(self):
        """Test the desktop launcher and actual GUI launch."""
        try:
            # Check launcher script
            launcher_script = os.path.join(self.test_home, ".local/bin/notebook-launcher")
            if not os.path.exists(launcher_script):
                self.log("Launcher script not found", error=True)
                return False
                
            if not os.access(launcher_script, os.X_OK):
                self.log("Launcher script is not executable", error=True)
                return False
            
            # Check desktop file
            desktop_path = os.path.join(self.test_home, ".local/share/applications/notebook.desktop")
            if not os.path.exists(desktop_path):
                self.log("Desktop entry not found", error=True)
                return False
            
            # Read and verify desktop entry
            with open(desktop_path, 'r') as f:
                desktop_content = f.read()
                
            required_fields = {
                'Type': 'Application',
                'Name': 'Note Book',
                'Exec': os.path.join(self.test_home, '.local/bin/notebook-launcher')
            }
            
            for key, value in required_fields.items():
                if f"{key}={value}" not in desktop_content:
                    self.log(f"Desktop entry missing or incorrect {key}: {value}", error=True)
                    return False
            
            # Test GUI launch
            env = os.environ.copy()
            env["DISPLAY"] = os.getenv("DISPLAY", ":0")  # Use current display or :0
            env["ROOTFS_DIR"] = os.path.join(self.test_home, ".local/share/notebook_rootfs")
            env["GSETTINGS_SCHEMA_DIR"] = os.path.join(self.test_home, ".local/share/notebook")
            
            # Launch the application
            try:
                process = subprocess.Popen(
                    [launcher_script],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait a bit for the GUI to launch
                time.sleep(3)
                
                # Check if process is still running
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    self.log(f"Application failed to start or crashed immediately", error=True)
                    self.log(f"stdout: {stdout.decode()}", error=True)
                    self.log(f"stderr: {stderr.decode()}", error=True)
                    return False
                
                # Try to communicate with the app using DBus or check window presence
                try:
                    import Xlib.display
                    display = Xlib.display.Display()
                    root = display.screen().root
                    window_ids = root.get_full_property(
                        display.intern_atom('_NET_CLIENT_LIST'),
                        display.intern_atom('WINDOW')
                    ).value.tolist()
                    
                    app_window_found = False
                    for window_id in window_ids:
                        window = display.create_resource_object('window', window_id)
                        name = window.get_wm_name()
                        if name and "Note Book" in name:
                            app_window_found = True
                            break
                    
                    if not app_window_found:
                        self.log("Application window not found", error=True)
                        return False
                        
                except ImportError:
                    self.log("Warning: python3-xlib not available, skipping window presence check")
                
                # Clean shutdown
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    self.log("Warning: Application had to be forcefully terminated")
                
                if process.returncode not in [0, -15]:  # 0 or terminated by signal 15 (SIGTERM)
                    self.log(f"Application exited with unexpected code: {process.returncode}", error=True)
                    return False
                
            except Exception as e:
                self.log(f"GUI launch test failed: {str(e)}", error=True)
                return False
            
            self.log("Launcher and GUI verification successful")
            return True
            
        except Exception as e:
            self.log(f"Launcher verification failed: {str(e)}", error=True)
            return False

    def cleanup(self):
        """Clean up the test environment."""
        try:
            subprocess.run(["rm", "-rf", self.test_home], check=True)
            self.log("Cleaned up test environment")
        except Exception as e:
            self.log(f"Cleanup failed: {str(e)}", error=True)

    def run_all_tests(self):
        """Run all installation tests."""
        try:
            if not self.setup_test_environment():
                return False
            
            if not self.verify_dependencies():
                return False
            
            if not self.run_installer():
                return False
            
            if not self.verify_files():
                return False
            
            if not self.verify_launcher():
                return False
            
            return self.success
            
        finally:
            self.cleanup()
            
            # Save test results
            results = {
                "success": self.success,
                "logs": self.logs,
                "errors": self.errors,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open("installer_test_results.json", "w") as f:
                json.dump(results, f, indent=2)

if __name__ == "__main__":
        
    tester = InstallerTester()
    success = tester.run_all_tests()
    
    # Print results (for CI/CD)
    print("\n=== Test Results ===")
    print(f"Success: {success}")
    print("\nErrors:")
    for error in tester.errors:
        print(f"  {error}")
    
    sys.exit(0 if success else 1)