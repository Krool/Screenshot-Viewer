import subprocess
import sys
from pathlib import Path

def build():
    """Build the application using PyInstaller."""
    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--icon=assets/icons/app_icon.ico",
        "--name=GameScreenshotViewer",
        "src/app/main.py"
    ], check=True)

if __name__ == "__main__":
    build() 