from PyQt6.QtWidgets import QMainWindow
from ..utils.logger import setup_logging

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Screenshot Viewer")
        self.resize(1200, 800)
        setup_logging()
        # ... rest of window initialization ... 