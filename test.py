import sys
from PyQt6.QtWidgets import QApplication, QLabel

print("Starting application...")
app = QApplication(sys.argv)

print("Creating label...")
label = QLabel("Hello World!")

print("Showing label...")
label.show()

print("Entering event loop...")
sys.exit(app.exec()) 