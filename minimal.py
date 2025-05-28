import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle('Minimal Test')

layout = QVBoxLayout()
label = QLabel('Hello World')
layout.addWidget(label)

window.setLayout(layout)
window.resize(250, 150)
window.show()

sys.exit(app.exec()) 