"""
Main module for the Steam Screenshots Viewer application.
Contains the application entry point.
"""

import sys
from PyQt6.QtWidgets import QApplication
from .viewer import SteamScreenshotsViewer

def main():
    app = QApplication(sys.argv)
    viewer = SteamScreenshotsViewer()
    viewer.show()
    sys.exit(app.exec()) 