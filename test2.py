import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt

print("Starting application...")
app = QApplication(sys.argv)

print("Creating window...")
window = QMainWindow()
window.setWindowTitle("Test Window")
window.setGeometry(100, 100, 400, 200)

print("Creating label...")
label = QLabel("Hello World!", window)
label.setAlignment(Qt.AlignmentFlag.AlignCenter)
window.setCentralWidget(label)

print("Showing window...")
window.show()

print("Entering event loop...")
app.exec() 