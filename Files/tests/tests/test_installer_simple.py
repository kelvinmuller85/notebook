#!/usr/bin/env python3
"""
Simplified installer test that works in minimal environments.
"""

import os
import sys
import subprocess
import json
import tempfile
import time
from pathlib import Path

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
        print(log_entry)

    def setup_test_environment(self):
        """Create a minimal test environment."""
        try:
            self.test_home = tempfile.mkdtemp(prefix="notebook_test_")
            self.log(f"Created test environment at: {self.test_home}")
            
            # Create XDG directories
            for dir_name in [".local/share/notebook", 
                           ".local/bin",
                           ".config/notebook",
                           ".local/share/applications",
                           ".local/share/notebook/glib-2.0/schemas"]:
                os.makedirs(os.path.join(self.test_home, dir_name), exist_ok=True)
                
            # Create minimal test files
            notebook_dir = os.path.join(self.test_home, ".local/share/notebook")
            os.makedirs(os.path.join(notebook_dir, "Files"), exist_ok=True)
            with open(os.path.join(notebook_dir, "Files/test_file.py"), 'w') as f:
                f.write('print("Test file")\n')
            
            # Create rootfs structure
            rootfs_dir = os.path.join(self.test_home, ".local/share/notebook_rootfs")
            for subdir in ["usr/bin", "usr/lib", "opt/notebook_venv/bin"]:
                os.makedirs(os.path.join(rootfs_dir, subdir), exist_ok=True)
            
            # Create dummy schema file
            schema_path = os.path.join(self.test_home, 
                                     ".local/share/notebook/glib-2.0/schemas",
                                     "org.x.sticky.gschema.xml")
            with open(schema_path, 'w') as f:
                f.write("""<?xml version="1.0" encoding="UTF-8"?>
<schemalist>
  <schema path="/org/x/sticky/" id="org.x.sticky">
    <key type="s" name="theme">
      <default>'light'</default>
      <summary>Theme</summary>
    </key>
  </schema>
</schemalist>""")
            
            # Create minimal venv structure
            venv_dir = os.path.join(rootfs_dir, "opt/notebook_venv")
            os.makedirs(os.path.join(venv_dir, "lib/python3/site-packages"), exist_ok=True)
            with open(os.path.join(venv_dir, "bin/python3"), 'w') as f:
                f.write("#!/bin/sh\npython3 \"$@\"")
            os.chmod(os.path.join(venv_dir, "bin/python3"), 0o755)
            
            # Set environment
            os.environ.update({
                "HOME": self.test_home,
                "XDG_DATA_HOME": os.path.join(self.test_home, ".local/share"),
                "XDG_CONFIG_HOME": os.path.join(self.test_home, ".config"),
                "NOTEBOOK_TEST_MODE": "1"
            })
            
            return True
            
        except Exception as e:
            self.log(f"Failed to set up test environment: {str(e)}", error=True)
            return False

    def run_installer(self):
        """Run the installation script."""
        try:
            script_dir = Path(__file__).parent.parent
            install_script = script_dir / "usb-installer/install.sh"
            
            result = subprocess.run(["bash", str(install_script)],
                                 env=os.environ,
                                 cwd=self.test_home,
                                 capture_output=True,
                                 text=True)
            
            # Log output
            for line in result.stdout.splitlines():
                self.log(f"INSTALLER: {line}")
            for line in result.stderr.splitlines():
                if "ERROR:" in line:
                    self.log(line, error=True)
                else:
                    self.log(f"INSTALLER ERR: {line}")
            
            return result.returncode == 0
            
        except Exception as e:
            self.log(f"Failed to run installer: {str(e)}", error=True)
            return False

    def verify_files(self):
        """Check that critical files exist."""
        required_paths = [
            ".local/share/notebook/Files",
            ".local/share/applications/notebook.desktop",
            ".local/bin/notebook-launcher",
            ".config/notebook"
        ]
        
        success = True
        for path in required_paths:
            full_path = os.path.join(self.test_home, path)
            if not os.path.exists(full_path):
                self.log(f"Missing required path: {path}", error=True)
                success = False
            else:
                self.log(f"Verified path exists: {path}")
        
        return success

    def cleanup(self):
        """Clean up test files."""
        try:
            if self.test_home:
                subprocess.run(["rm", "-rf", self.test_home], check=False)
        except:
            pass

    def run_tests(self):
        """Run all installation tests."""
        try:
            self.log("Setting up test environment...")
            if not self.setup_test_environment():
                return False
            
            self.log("Running installer...")
            if not self.run_installer():
                return False
            
            self.log("Verifying installation...")
            if not self.verify_files():
                return False
            
            return self.success
            
        finally:
            self.cleanup()
            
            # Save results
            results = {
                "success": self.success,
                "logs": self.logs,
                "errors": self.errors,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open("installer_test_results.json", "w") as f:
                json.dump(results, f, indent=2)

def main():
    tester = InstallerTester()
    success = tester.run_tests()
    
    print("\n=== Test Results ===")
    print(f"Success: {success}")
    if not success:
        print("\nErrors:")
        for error in tester.errors:
            print(f"  {error}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()