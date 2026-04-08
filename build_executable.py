"""
build_executable.py — PyInstaller script for kjudge.

Use this script to compile kjudge into a single, standalone executable
that does not require the user to have Python installed.

Prerequisites:
  pip install pyinstaller

Usage:
  python build_executable.py

The resulting executable will be placed in the `dist/` directory.
"""

import os
import subprocess
import sys

def main():
    print("Building standalone executable for kjudge...")
    
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller is not installed.")
        print("Run: pip install pyinstaller")
        sys.exit(1)

    # We use kjudge.__main__ as the entrypoint for PyInstaller
    entry_script = os.path.join("kjudge", "__main__.py")
    
    if not os.path.exists(entry_script):
        print(f"Error: Could not find {entry_script}")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "kjudge",
        "--onefile",
        "--console",
        "--clean",
        entry_script
    ]

    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    print("\n✓ Build complete! Executable is located in the 'dist' folder.")

if __name__ == "__main__":
    main()
