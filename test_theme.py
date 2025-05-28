import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        print("Creating test window...")
        super().__init__()
        self.setWindowTitle("Theme Test")
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Create layout
        layout = QVBoxLayout(central)
        
        # Add label
        label = QLabel("Testing Window Theme")
        label.setStyleSheet("color: black; font-size: 24px;")
        layout.addWidget(label)
        
        # Set size and position
        self.resize(400, 300)
        self.move(100, 100)

def main():
    try:
        print("Starting test application...")
        app = QApplication(sys.argv)
        print("QApplication created")
        
        # Create and show window
        window = TestWindow()
        print("Window created")
        window.show()
        print("Window shown")
        
        # Keep window reference
        app.window = window
        
        print("Starting event loop...")
        return app.exec()
    except Exception as e:
        print(f"Error in main(): {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    print("Starting theme test...")
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 