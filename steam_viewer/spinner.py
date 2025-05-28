"""
Loading spinner widget implementation.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTimer

class LoadingSpinner(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(24, 24)
        self.setText("⟳")  # Using a unicode character for the spinner
        self.setStyleSheet("""
            color: #66c0f4;
            font-size: 18px;
            background: transparent;
        """)
        self.hide()

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.setStyleSheet(f"""
            color: #66c0f4;
            font-size: 18px;
            background: transparent;
            transform: rotate({self.angle}deg);
        """)

    def start(self):
        self.show()
        self.timer.start(100)

    def stop(self):
        self.timer.stop()
        self.hide() 