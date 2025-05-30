from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QPropertyAnimation, Qt

class Toast(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background-color: #1b2838;
                border: 1px solid #66c0f4;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        
        self.message_label = QLabel()
        self.message_label.setStyleSheet("""
            color: #c7d5e0;
            font-size: 12px;
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.addWidget(self.message_label)
        layout.addWidget(self.container)
        
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(2000)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        
    def show_message(self, message):
        self.message_label.setText(message)
        self.adjustSize()
        self.show()
        self.animation.start() 