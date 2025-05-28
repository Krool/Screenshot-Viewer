import sys
import os
import datetime
import json
import requests
import subprocess
import ctypes
import glob
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QListWidget, QLabel, QScrollArea, QListWidgetItem,
                            QPushButton, QHBoxLayout, QLineEdit, QMessageBox,
                            QSplitter, QTabWidget)
from PyQt6.QtGui import QPixmap, QImage, QIcon, QPalette, QColor, QFont, QCursor, QMovie, QTransform
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QPoint, pyqtProperty, QEasingCurve

def set_window_theme(window):
    """Set dark theme for Windows title bar"""
    if sys.platform != 'win32':
        return
        
    try:
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        
        value = ctypes.c_int(2)
        set_window_attribute(window.winId().__int__(), 
                           DWMWA_USE_IMMERSIVE_DARK_MODE,
                           ctypes.byref(value),
                           ctypes.sizeof(value))
    except Exception as e:
        print(f"Error setting window theme: {e}")

class SteamGameDatabase:
    def __init__(self):
        self.games = {}
        self.cache_file = os.path.join(os.path.dirname(__file__), 'steam_games_cache.json')
        self.load_cache()

    def load_cache(self):
        """Load game data from cache file if it exists and is less than 7 days old"""
        try:
            if os.path.exists(self.cache_file):
                cache_age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(self.cache_file))
                if cache_age.days < 7:  # Cache is valid for 7 days
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        self.games = json.load(f)
                        return True
        except Exception as e:
            print(f"Error loading cache: {e}")
        return False

    def save_cache(self):
        """Save game data to cache file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.games, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def update_database(self):
        """Fetch latest game list from Steam API"""
        try:
            response = requests.get('https://api.steampowered.com/ISteamApps/GetAppList/v2/')
            if response.status_code == 200:
                data = response.json()
                self.games = {str(app['appid']): app['name'] for app in data['applist']['apps']}
                self.save_cache()
                return True
        except Exception as e:
            print(f"Error updating database: {e}")
        return False

    def get_game_name(self, app_id):
        """Get game name from app ID"""
        # If games dict is empty, try to update it
        if not self.games:
            self.update_database()
        return self.games.get(str(app_id), f"Unknown Game (ID: {app_id})")

class LoadingSpinner(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(24, 24)
        self.setText("⟳")  # Using a unicode character for the spinner
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            color: #66c0f4;
            font-size: 18px;
            background: transparent;
        """)
        self.hide()

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        # Create rotation animation
        rotation = QPropertyAnimation(self, b"rotation")
        rotation.setDuration(100)  # Duration matches timer interval
        rotation.setStartValue(self.angle - 30)
        rotation.setEndValue(self.angle)
        rotation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    @pyqtProperty(int)
    def rotation(self):
        return self.angle

    @rotation.setter
    def rotation(self, angle):
        self.angle = angle
        # Use HTML entity for the arrow and rotate it using CSS transform
        self.setText(f'<div style="transform: rotate({angle}deg);">⟳</div>')

    def start(self):
        self.show()
        self.timer.start(100)

    def stop(self):
        self.timer.stop()
        self.hide()

class LoadingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set size and position
        self.setFixedSize(200, 200)
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                 (screen.height() - self.height()) // 2)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create container widget with background
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #1b2838;
                border: 2px solid #66c0f4;
                border-radius: 10px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create spinning animation
        self.spinner = LoadingSpinner(self)
        self.spinner.setFixedSize(64, 64)
        
        # Add loading text
        loading_text = QLabel("Loading Screenshots...")
        loading_text.setStyleSheet("""
            color: #66c0f4;
            font-family: "Motiva Sans", Arial, Helvetica, sans-serif;
            font-size: 14px;
            margin-top: 10px;
        """)
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        container_layout.addWidget(self.spinner)
        container_layout.addWidget(loading_text)
        layout.addWidget(container)
        
        # Start the spinner
        self.spinner.start()
        
    def closeEvent(self, event):
        self.spinner.stop()
        super().closeEvent(event)

class SteamScreenshotsViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing main window...")
        
        # Initialize game database
        self.game_db = SteamGameDatabase()
        self.game_tabs = {}  # Store game tabs by ID
        
        # Basic window setup
        self.setWindowTitle("Steam Screenshots Viewer")
        self.resize(1200, 800)  # Larger default size for split view
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        
        # Create header with status and refresh button
        header_layout = QHBoxLayout()
        self.status_label = QLabel("Loading...")
        self.status_label.setStyleSheet("color: white; font-size: 14px;")
        header_layout.addWidget(self.status_label)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2a475e;
                color: #c7d5e0;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #66c0f4;
                color: #1b2838;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_screenshots)
        header_layout.addWidget(self.refresh_button)
        
        self.main_layout.addLayout(header_layout)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Tab widget with screenshots
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Create the tab widget for screenshots
        self.tab_widget = QTabWidget()
        left_layout.addWidget(self.tab_widget)
        
        # Create the "All" tab with a list widget
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(200, 200))
        self.list_widget.setSpacing(10)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.itemClicked.connect(self.on_screenshot_clicked)
        
        # Add the list widget to a tab
        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)
        all_layout.addWidget(self.list_widget)
        self.tab_widget.addTab(all_tab, "All")
        
        # Right side: Preview and details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Preview area
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.preview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_scroll.setWidget(self.preview_label)
        
        # Details area
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        
        self.game_name_label = QLabel()
        self.game_name_label.setStyleSheet("color: #66c0f4; font-size: 16px; font-weight: bold;")
        details_layout.addWidget(self.game_name_label)
        
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #c7d5e0;")
        details_layout.addWidget(self.date_label)
        
        self.resolution_label = QLabel()
        self.resolution_label.setStyleSheet("color: #c7d5e0;")
        details_layout.addWidget(self.resolution_label)
        
        self.file_size_label = QLabel()
        self.file_size_label.setStyleSheet("color: #c7d5e0;")
        details_layout.addWidget(self.file_size_label)
        
        # Add preview and details to right layout
        right_layout.addWidget(self.preview_scroll, stretch=3)
        right_layout.addWidget(self.details_widget, stretch=1)
        
        # Add widgets to splitter
        self.main_splitter.addWidget(left_widget)
        self.main_splitter.addWidget(right_widget)
        
        # Set initial splitter sizes (40% left, 60% right)
        self.main_splitter.setSizes([400, 600])
        
        # Add splitter to main layout
        self.main_layout.addWidget(self.main_splitter)
        
        # Create loading window
        self.loading_window = LoadingWindow()
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1b2838;
            }
            QTabWidget::pane {
                border: none;
                background: #1b2838;
            }
            QTabBar::tab {
                background: #2a475e;
                color: #c7d5e0;
                padding: 8px 16px;
                border: none;
            }
            QTabBar::tab:selected {
                background: #66c0f4;
                color: #1b2838;
            }
            QListWidget {
                background-color: #1b2838;
                border: none;
            }
            QListWidget::item {
                background-color: #2a475e;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #2a475e;
                border: 2px solid #66c0f4;
            }
            QScrollArea {
                border: 1px solid #2a475e;
                border-radius: 3px;
            }
            QScrollBar {
                background: #1b2838;
                width: 12px;
                height: 12px;
            }
            QScrollBar::handle {
                background: #2a475e;
                border-radius: 6px;
            }
            QScrollBar::handle:hover {
                background: #66c0f4;
            }
        """)
        
        print("Basic UI setup complete")
        
        # Schedule screenshot loading
        QTimer.singleShot(100, self.load_screenshots)

    def refresh_screenshots(self):
        """Refresh the screenshots list"""
        self.loading_window.show()
        self.list_widget.clear()
        # Clear game tabs except "All"
        while self.tab_widget.count() > 1:
            self.tab_widget.removeTab(1)
        self.game_tabs.clear()
        self.load_screenshots()

    def create_game_tab(self, game_id, game_name):
        """Create a new tab for a game if it doesn't exist"""
        if game_id not in self.game_tabs:
            # Create new list widget for the game
            game_list = QListWidget()
            game_list.setViewMode(QListWidget.ViewMode.IconMode)
            game_list.setIconSize(QSize(200, 200))
            game_list.setSpacing(10)
            game_list.setMovement(QListWidget.Movement.Static)
            game_list.itemClicked.connect(self.on_screenshot_clicked)
            
            # Create tab widget
            game_tab = QWidget()
            game_layout = QVBoxLayout(game_tab)
            game_layout.addWidget(game_list)
            
            # Add tab
            self.tab_widget.addTab(game_tab, game_name)
            self.game_tabs[game_id] = game_list
            
        return self.game_tabs[game_id]

    def on_screenshot_clicked(self, item):
        """Handle screenshot selection"""
        screenshot_path = item.data(Qt.ItemDataRole.UserRole)
        if screenshot_path:
            print(f"Selected screenshot: {screenshot_path}")
            
            # Update preview
            pixmap = QPixmap(screenshot_path)
            scaled_pixmap = pixmap.scaled(
                self.preview_scroll.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
            
            # Update details
            try:
                # Get game name
                game_id = screenshot_path.split("remote\\")[1].split("\\")[0]
                game_name = self.game_db.get_game_name(game_id)
                self.game_name_label.setText(game_name)
                
                # Get file info
                file_info = os.stat(screenshot_path)
                date = datetime.datetime.fromtimestamp(file_info.st_mtime)
                size = file_info.st_size / (1024 * 1024)  # Convert to MB
                
                # Get image resolution
                image = QImage(screenshot_path)
                resolution = f"{image.width()} x {image.height()}"
                
                # Update labels
                self.date_label.setText(f"Date: {date.strftime('%Y-%m-%d %H:%M:%S')}")
                self.resolution_label.setText(f"Resolution: {resolution}")
                self.file_size_label.setText(f"Size: {size:.2f} MB")
                
            except Exception as e:
                print(f"Error updating details: {e}")

    def load_screenshots(self):
        print("Loading screenshots...")
        self.status_label.setText("Loading screenshots...")
        self.loading_window.show()
        
        try:
            # Get the default Steam screenshots path
            steam_path = os.path.expandvars(r"%ProgramFiles(x86)%\Steam")
            userdata_path = os.path.join(steam_path, "userdata")
            
            if not os.path.exists(userdata_path):
                self.status_label.setText("Steam userdata folder not found!")
                self.loading_window.close()
                return
                
            # Find all screenshot folders
            screenshots = []
            for user_folder in os.listdir(userdata_path):
                screenshots_path = os.path.join(userdata_path, user_folder, "760", "remote", "*", "screenshots")
                screenshot_folders = glob.glob(screenshots_path)
                
                for folder in screenshot_folders:
                    screenshots.extend(glob.glob(os.path.join(folder, "*.jpg")))
                    screenshots.extend(glob.glob(os.path.join(folder, "*.png")))
            
            if not screenshots:
                self.status_label.setText("No screenshots found!")
                self.loading_window.close()
                return
            
            # Sort screenshots by modification time (newest first)
            screenshots.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Add screenshots to the list and game tabs
            for screenshot in screenshots:
                # Create item for main list
                item = QListWidgetItem()
                pixmap = QPixmap(screenshot)
                icon = QIcon(pixmap)
                item.setIcon(icon)
                item.setData(Qt.ItemDataRole.UserRole, screenshot)
                self.list_widget.addItem(item)
                
                # Add to game tab
                try:
                    game_id = screenshot.split("remote\\")[1].split("\\")[0]
                    game_name = self.game_db.get_game_name(game_id)
                    game_list = self.create_game_tab(game_id, game_name)
                    
                    # Create item for game tab
                    game_item = QListWidgetItem()
                    game_item.setIcon(icon)
                    game_item.setData(Qt.ItemDataRole.UserRole, screenshot)
                    game_list.addItem(game_item)
                except Exception as e:
                    print(f"Error adding to game tab: {e}")
            
            self.status_label.setText(f"Found {len(screenshots)} screenshots")
            print(f"Loaded {len(screenshots)} screenshots")
            
        except Exception as e:
            self.status_label.setText(f"Error loading screenshots: {str(e)}")
            print(f"Error loading screenshots: {str(e)}")
        
        finally:
            self.loading_window.close()

# Simple main function similar to the working examples
app = QApplication(sys.argv)
app.setStyle('Fusion')  # Set Fusion style for better dark theme support
window = SteamScreenshotsViewer()
window.show()
sys.exit(app.exec()) 