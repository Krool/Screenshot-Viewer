import os
import sys
import logging

# Enhanced debug output system
class DebugConsole:
    @staticmethod
    def log(*args, **kwargs):
        """Log to console only when not running as a bundled executable"""
        if not getattr(sys, 'frozen', False):
            print("[DEBUG]", *args, **kwargs)
    
    @staticmethod
    def error(*args, **kwargs):
        """Log errors to console only when not bundled"""
        if not getattr(sys, 'frozen', False):
            print("[ERROR]", *args, file=sys.stderr, **kwargs)

# Completely suppress console output when frozen
if getattr(sys, 'frozen', False):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    # Also disable any existing console handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)

# Configure logging to file only
log_dir = os.path.join(os.getenv('APPDATA'), 'Game Screenshot Viewer', 'Logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,  # Reduced from DEBUG to minimize logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(os.path.join(log_dir, 'debug.log'))]
)

import sys
import datetime
import json
import requests
import subprocess
import ctypes
import glob
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QListWidget, QLabel, QScrollArea, QListWidgetItem,
                            QPushButton, QHBoxLayout, QLineEdit, QMessageBox,
                            QSplitter, QTabWidget, QFrame, QProgressBar, QComboBox,
                            QSizePolicy)
from PyQt6.QtGui import (QPixmap, QImage, QIcon, QPalette, QColor, QFont, 
                        QCursor, QMovie, QTransform, QGuiApplication)
from PyQt6.QtCore import (Qt, QSize, QTimer, QPropertyAnimation, QPoint, 
                         pyqtProperty, QEasingCurve, QRect)

def set_window_theme(window):
    """Set dark theme for Windows title bar"""
    if sys.platform == 'win32':
        try:
            # Enable dark mode for title bar
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            value = ctypes.c_int(2)
            set_window_attribute(window.winId().__int__(), 
                               DWMWA_USE_IMMERSIVE_DARK_MODE,
                               ctypes.byref(value),
                               ctypes.sizeof(value))
            
            # Set title bar color
            DWMWA_CAPTION_COLOR = 35
            caption_color = ctypes.c_uint(0x001B2838)  # Steam dark blue
            set_window_attribute(window.winId().__int__(),
                               DWMWA_CAPTION_COLOR,
                               ctypes.byref(caption_color),
                               ctypes.sizeof(caption_color))
        except Exception as e:
            print(f"Error setting window theme: {e}")

class SteamProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 6)  # Steam-like thin progress bar
        self.setTextVisible(False)
        self.setStyleSheet("""
            QProgressBar {
                background-color: #1b2838;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #66c0f4;
                border-radius: 3px;
            }
        """)

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create container widget with background
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background-color: #1b2838;
                border: 2px solid #66c0f4;
                border-radius: 10px;
            }
        """)
        self.container.setFixedSize(400, 100)
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Loading text
        self.loading_text = QLabel("Loading Screenshots...")
        self.loading_text.setStyleSheet("""
            color: #66c0f4;
            font-family: "Motiva Sans", Arial, Helvetica, sans-serif;
            font-size: 14px;
            margin-bottom: 10px;
        """)
        self.loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress_bar = SteamProgressBar()
        
        container_layout.addWidget(self.loading_text)
        container_layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Add container to a centered layout
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(self.container)
        center_layout.addStretch()
        
        # Add vertical centering
        layout.addStretch()
        layout.addLayout(center_layout)
        layout.addStretch()
        
        # Set semi-transparent dark background
        self.setStyleSheet("""
            LoadingOverlay {
                background-color: rgba(0, 0, 0, 180);
            }
        """)
    
    def set_progress(self, value, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(value)
        self.loading_text.setText(f"Loading Screenshots... ({value}/{total})")
        QApplication.processEvents()  # Force UI update
    
    def center_in_parent(self):
        if self.parentWidget():
            parent_rect = self.parentWidget().rect()
            self.setGeometry(parent_rect)
            
            # Calculate center position for container
            container_x = (parent_rect.width() - self.container.width()) // 2
            container_y = (parent_rect.height() - self.container.height()) // 2
            self.container.move(container_x, container_y)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()  # Ensure overlay stays on top
        self.center_in_parent()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.center_in_parent()

class GameNameEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create container widget with background
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #1b2838;
                border: 2px solid #66c0f4;
                border-radius: 10px;
            }
        """)
        container.setFixedSize(400, 150)
        container_layout = QVBoxLayout(container)
        
        # Add title
        title = QLabel("Edit Game Name")
        title.setStyleSheet("""
            color: #66c0f4;
            font-size: 16px;
            font-weight: bold;
            padding: 5px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)
        
        # Add game name input
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a475e;
                color: #c7d5e0;
                border: 1px solid #66c0f4;
                border-radius: 3px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        container_layout.addWidget(self.name_input)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        button_style = """
            QPushButton {
                background-color: #2a475e;
                color: #c7d5e0;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #66c0f4;
                color: #1b2838;
            }
        """
        
        self.save_button.setStyleSheet(button_style)
        self.cancel_button.setStyleSheet(button_style)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        container_layout.addLayout(button_layout)
        layout.addWidget(container)
        
        # Set semi-transparent dark background
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        
        # Connect buttons
        self.cancel_button.clicked.connect(self.close)
        
        # Center on parent
        if parent:
            self.move(
                parent.window().frameGeometry().center() - self.frameGeometry().center()
            )

class SteamGameDatabase:
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger('SteamGameDatabase')
        
        self.games = {}
        self.custom_games = {}
        self.pending_updates = set()  # Track new game IDs for batch updates
        
        # Determine if we're running in a bundled exe
        if getattr(sys, 'frozen', False):
            # Running in a bundle
            self.base_path = os.path.dirname(sys.executable)
            # Load baseline cache files that were included in the build
            self.baseline_cache = os.path.join(self.base_path, 'steam_games_cache.json')
            self.baseline_custom = os.path.join(self.base_path, 'custom_games_cache.json')
            # User-specific cache files will be stored in AppData
            appdata = os.getenv('APPDATA')
            if appdata:
                cache_dir = os.path.join(appdata, 'Game Screenshot Viewer')
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir)
                self.cache_file = os.path.join(cache_dir, 'steam_games_cache.json')
                self.custom_cache_file = os.path.join(cache_dir, 'custom_games_cache.json')
            else:
                self.cache_file = os.path.join(self.base_path, 'steam_games_cache.json')
                self.custom_cache_file = os.path.join(self.base_path, 'custom_games_cache.json')
        else:
            # Running from source
            self.base_path = os.path.dirname(__file__)
            self.baseline_cache = os.path.join(self.base_path, 'steam_games_cache.json')
            self.baseline_custom = os.path.join(self.base_path, 'custom_games_cache.json')
            self.cache_file = self.baseline_cache
            self.custom_cache_file = self.baseline_custom
        
        self.logger.debug(f"Cache file path: {self.cache_file}")
        self.logger.debug(f"Custom cache file path: {self.custom_cache_file}")
        self.logger.debug(f"Baseline cache path: {self.baseline_cache}")
        
        # Load baseline data first
        self.load_baseline_cache()
        # Then load user-specific cache which may override baseline data
        self.load_cache()
        self.load_custom_cache()

    def load_baseline_cache(self):
        """Load the baseline cache that was included with the build"""
        try:
            if os.path.exists(self.baseline_cache):
                with open(self.baseline_cache, 'r', encoding='utf-8') as f:
                    baseline_games = json.load(f)
                    self.games.update(baseline_games)
                    self.logger.debug(f"Loaded {len(baseline_games)} games from baseline cache")
            if os.path.exists(self.baseline_custom):
                with open(self.baseline_custom, 'r', encoding='utf-8') as f:
                    baseline_custom = json.load(f)
                    self.custom_games.update(baseline_custom)
                    self.logger.debug(f"Loaded {len(baseline_custom)} custom games from baseline")
        except Exception as e:
            self.logger.error(f"Error loading baseline cache: {e}")

    def load_cache(self):
        """Load game data from cache file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.games = json.load(f)
                    self.logger.debug(f"Loaded {len(self.games)} games from cache")
                    return True
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")
            self.games = {}
        return False

    def save_cache(self):
        """Save game data to cache file"""
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.games, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Saved {len(self.games)} games to cache")
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")

    def load_custom_cache(self):
        """Load custom game names from cache file"""
        try:
            if os.path.exists(self.custom_cache_file):
                with open(self.custom_cache_file, 'r', encoding='utf-8') as f:
                    self.custom_games = json.load(f)
                    self.logger.debug(f"Loaded {len(self.custom_games)} custom game names")
        except Exception as e:
            self.logger.error(f"Error loading custom cache: {e}")
            self.custom_games = {}

    def save_custom_cache(self):
        """Save custom game names to cache file"""
        try:
            custom_cache_dir = os.path.dirname(self.custom_cache_file)
            if not os.path.exists(custom_cache_dir):
                os.makedirs(custom_cache_dir)
            with open(self.custom_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_games, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Saved {len(self.custom_games)} custom game names")
        except Exception as e:
            self.logger.error(f"Error saving custom cache: {e}")

    def update_database(self):
        """Fetch latest game list from Steam API"""
        try:
            response = requests.get('https://api.steampowered.com/ISteamApps/GetAppList/v2/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                new_games = {str(app['appid']): app['name'] for app in data['applist']['apps']}
                
                # Update only if we have new data
                if new_games:
                    self.games.update(new_games)
                    self.save_cache()
                return True
        except (requests.RequestException, Exception) as e:
            self.logger.error(f"Error updating database (working offline): {e}")
        return False

    def queue_update_for_id(self, app_id):
        """Queue a game ID for future update"""
        if app_id not in self.games and app_id not in self.custom_games:
            self.pending_updates.add(str(app_id))
            # Try to update if we have enough pending updates
            if len(self.pending_updates) >= 10:
                self.process_pending_updates()

    def process_pending_updates(self):
        """Process any pending game ID updates"""
        if not self.pending_updates:
            return

        try:
            # Convert set to list for string joining
            ids = list(self.pending_updates)
            # Steam Web API for batch game details
            url = f"https://store.steampowered.com/api/appdetails?appids={','.join(ids)}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                updated = False
                
                for app_id in ids:
                    if app_id in data and data[app_id].get('success'):
                        name = data[app_id]['data'].get('name')
                        if name:
                            self.games[app_id] = name
                            updated = True
                
                if updated:
                    self.save_cache()
                
                # Clear processed IDs
                self.pending_updates.clear()
                
        except (requests.RequestException, Exception) as e:
            self.logger.error(f"Error processing pending updates (working offline): {e}")

    def get_game_name(self, app_id):
        """Get game name from app ID"""
        app_id = str(app_id)
        self.logger.debug(f"Looking up game name for ID: {app_id}")
        
        # Check custom names first
        if app_id in self.custom_games:
            self.logger.debug(f"Found custom name for {app_id}: {self.custom_games[app_id]}")
            return self.custom_games[app_id]
        
        # Check main database
        if app_id in self.games:
            self.logger.debug(f"Found cached name for {app_id}: {self.games[app_id]}")
            return self.games[app_id]
        
        # Try to get name from Steam API
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get(app_id, {}).get('success'):
                    name = data[app_id]['data'].get('name')
                    if name:
                        self.logger.debug(f"Found name from API for {app_id}: {name}")
                        self.games[app_id] = name
                        self.save_cache()
                        return name
        except Exception as e:
            self.logger.error(f"Error fetching game name from API: {e}")
        
        # Queue for update if not found
        self.queue_update_for_id(app_id)
        
        unknown_name = f"Unknown Game (ID: {app_id})"
        self.logger.debug(f"Using fallback name: {unknown_name}")
        return unknown_name

    def set_custom_game_name(self, app_id, name):
        """Set a custom name for a game"""
        app_id = str(app_id)
        self.custom_games[app_id] = name
        self.save_custom_cache()
        # Remove from pending updates if it was queued
        self.pending_updates.discard(app_id)

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Create semi-transparent dark background
        self.setStyleSheet("""
            LoadingWindow {
                background-color: rgba(0, 0, 0, 180);
            }
        """)
        
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
        container.setFixedSize(200, 200)
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

    def showEvent(self, event):
        if self.parentWidget():
            # Center on parent
            self.resize(self.parentWidget().size())
            self.move(0, 0)
        super().showEvent(event)
        
    def closeEvent(self, event):
        self.spinner.stop()
        super().closeEvent(event)

class FullScreenPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        
        # Style the widget
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 220);
            }
            QLabel {
                background: transparent;
            }
        """)
        
        # Connect click event
        self.mousePressEvent = self.close_preview
    
    def show_image(self, image_path):
        # Get screen geometry
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Load and display image at original size
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap)
        
        self.showFullScreen()
    
    def close_preview(self, event):
        self.close()

class Toast(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create container widget with background
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background-color: #1b2838;
                border: 1px solid #66c0f4;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        
        # Add label for message
        self.message_label = QLabel()
        self.message_label.setStyleSheet("""
            color: #c7d5e0;
            font-size: 12px;
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.addWidget(self.message_label)
        layout.addWidget(self.container)
        
        # Set up animation
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(2000)  # 2 seconds
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        
        # Center on parent
        if parent:
            self.move(
                parent.width() - self.width() - 20,
                parent.height() - self.height() - 20
            )
    
    def show_message(self, message):
        self.message_label.setText(message)
        self.adjustSize()
        self.show()
        self.animation.start()

class SteamScreenshotsViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_sorting = False  # Add sorting lock flag
        self.logger = logging.getLogger('SteamScreenshotsViewer')
        
        # Initialize attributes
        self.current_screenshot = None  # Track selected screenshot
        self.game_db = SteamGameDatabase()
        self.game_tabs = {}
        
        # Window setup
        set_window_theme(self)
        self.setWindowTitle("Game Screenshot Viewer")
        self.resize(1200, 800)
        
        # Create proper central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header layout reorganization
        header_widget = QWidget()
        header_widget.setFixedHeight(40)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(5, 0, 5, 0)
        header_layout.setSpacing(10)

        # Game sorting group
        game_sort_group = QWidget()
        game_sort_layout = QHBoxLayout(game_sort_group)
        game_sort_layout.setContentsMargins(0, 0, 0, 0)
        game_sort_layout.setSpacing(5)
        
        game_label = QLabel("Sort Categories:")
        game_label.setStyleSheet("color: #c7d5e0; font-size: 12px;")
        game_sort_layout.addWidget(game_label)
        
        self.game_sort_combo = QComboBox()
        self.game_sort_combo.addItems(["Newest", "Oldest", "A to Z", "Z to A", "Screenshot Count"])
        self.game_sort_combo.setFixedWidth(120)
        self.game_sort_combo.setStyleSheet("""
            QComboBox {
                color: #c7d5e0;
                background-color: #2a475e;
                border: 1px solid #66c0f4;
                padding: 2px;
            }
            QComboBox QAbstractItemView {
                color: #c7d5e0;
                background-color: #2a475e;
                selection-background-color: #66c0f4;
            }
        """)
        game_sort_layout.addWidget(self.game_sort_combo)
        
        # Add screenshot sorting dropdown
        screenshot_label = QLabel("Sort Screenshots:")
        screenshot_label.setStyleSheet("color: #c7d5e0; font-size: 12px;")
        game_sort_layout.addWidget(screenshot_label)
        
        self.screenshot_sort_combo = QComboBox()
        self.screenshot_sort_combo.addItems(["Newest", "Oldest", "A to Z", "Z to A", "Largest", "Smallest"])
        self.screenshot_sort_combo.setCurrentIndex(0)  # Default to 'Newest First'
        self.screenshot_sort_combo.setFixedWidth(120)
        self.screenshot_sort_combo.setStyleSheet("""
            QComboBox {
                color: #c7d5e0;
                background-color: #2a475e;
                border: 1px solid #66c0f4;
                padding: 2px;
            }
            QComboBox QAbstractItemView {
                color: #c7d5e0;
                background-color: #2a475e;
                selection-background-color: #66c0f4;
            }
        """)
        game_sort_layout.addWidget(self.screenshot_sort_combo)
        self.screenshot_sort_combo.currentIndexChanged.connect(self.sort_screenshots)
        self.game_sort_combo.currentIndexChanged.connect(self.sort_game_tabs)
        
        header_layout.addWidget(game_sort_group)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #c7d5e0;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(self.status_label, stretch=1)
        
        # Refresh button
        self.refresh_button = QPushButton("⟳ Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                color: #c7d5e0;
                background-color: #2a475e;
                border: 1px solid #66c0f4;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #66c0f4;
                color: #1b2838;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_screenshots)
        header_layout.addWidget(self.refresh_button)

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setHandleWidth(8)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background: #2a475e;
                height: 8px;
            }
            QSplitter::handle:hover {
                background: #66c0f4;
            }
        """)
        
        # Create the tab widget for screenshots
        screenshots_widget = QWidget()
        screenshots_layout = QVBoxLayout(screenshots_widget)
        screenshots_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        screenshots_layout.addWidget(self.tab_widget)
        
        # Create the "All" tab with a list widget
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(200, 200))
        self.list_widget.setSpacing(10)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setMinimumHeight(220)  # Height of one item plus padding
        self.list_widget.itemClicked.connect(self.on_screenshot_clicked)
        
        # Add the list widget to a tab
        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)
        all_layout.setContentsMargins(0, 0, 0, 0)
        all_layout.addWidget(self.list_widget)
        self.tab_widget.addTab(all_tab, "All")
        
        # Create preview and details container
        self.preview_container = QWidget()
        preview_layout = QHBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scrollable area for all details
        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)
        details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        details_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create container for all details
        details_container = QWidget()
        details_container_layout = QVBoxLayout(details_container)
        
        # Game name section
        game_name_widget = QWidget()
        game_name_layout = QHBoxLayout(game_name_widget)
        game_name_layout.setContentsMargins(5, 0, 5, 0)
        
        self.game_name_label = QLabel()
        self.game_name_label.setStyleSheet("""
            color: #66c0f4; 
            font-size: 16px; 
            font-weight: bold;
            padding: 5px;
        """)
        self.game_name_label.setWordWrap(True)
        
        self.edit_game_name_button = QPushButton("✏️")
        self.edit_game_name_button.setFixedSize(24, 24)
        self.edit_game_name_button.setStyleSheet("""
            QPushButton {
                background-color: #2a475e;
                color: #c7d5e0;
                border: none;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #66c0f4;
                color: #1b2838;
            }
        """)
        self.edit_game_name_button.clicked.connect(self.edit_game_name)
        self.edit_game_name_button.hide()
        
        game_name_layout.addWidget(self.game_name_label)
        game_name_layout.addWidget(self.edit_game_name_button)
        details_container_layout.addWidget(game_name_widget)
        
        # Filename section
        filename_widget = QWidget()
        filename_layout = QHBoxLayout(filename_widget)
        filename_layout.setContentsMargins(5, 0, 5, 0)
        
        self.filename_edit = QLineEdit()
        self.filename_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2a475e;
                color: #c7d5e0;
                border: 1px solid #66c0f4;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        
        self.save_filename_button = QPushButton("💾")
        self.save_filename_button.setFixedSize(24, 24)
        self.save_filename_button.setStyleSheet("""
            QPushButton {
                background-color: #2a475e;
                color: #c7d5e0;
                border: none;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #66c0f4;
                color: #1b2838;
            }
        """)
        self.save_filename_button.clicked.connect(self.save_filename)
        
        filename_layout.addWidget(self.filename_edit)
        filename_layout.addWidget(self.save_filename_button)
        details_container_layout.addWidget(filename_widget)
        
        # File details
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #c7d5e0; padding: 5px;")
        details_container_layout.addWidget(self.date_label)
        
        self.resolution_label = QLabel()
        self.resolution_label.setStyleSheet("color: #c7d5e0; padding: 5px;")
        details_container_layout.addWidget(self.resolution_label)
        
        self.file_size_label = QLabel()
        self.file_size_label.setStyleSheet("color: #c7d5e0; padding: 5px;")
        details_container_layout.addWidget(self.file_size_label)
        
        # Action buttons
        button_style = """
            QPushButton {
                background-color: #2a475e;
                color: #c7d5e0;
                border: none;
                border-radius: 3px;
                padding: 8px;
                min-width: 120px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #66c0f4;
                color: #1b2838;
            }
        """
        
        self.open_location_button = QPushButton("📁 Open File Location")
        self.open_location_button.setStyleSheet(button_style)
        self.open_location_button.clicked.connect(self.open_file_location)
        details_container_layout.addWidget(self.open_location_button)
        
        self.copy_path_button = QPushButton("📋 Copy Image")
        self.copy_path_button.setStyleSheet(button_style)
        self.copy_path_button.clicked.connect(self.copy_image)
        details_container_layout.addWidget(self.copy_path_button)
        
        self.open_paint_button = QPushButton("🎨 Open in Paint")
        self.open_paint_button.setStyleSheet(button_style)
        self.open_paint_button.clicked.connect(self.open_in_paint)
        details_container_layout.addWidget(self.open_paint_button)
        
        # Add stretch to push content up
        details_container_layout.addStretch()
        
        # Set the container as the scroll area's widget
        details_scroll.setWidget(details_container)
        
        # Add scroll area to the preview layout
        preview_layout.addWidget(details_scroll)
        
        # Preview area
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        preview_frame.setStyleSheet("""
            QFrame {
                background-color: #1b2838;
                border: 1px solid #2a475e;
                border-radius: 3px;
            }
        """)
        preview_frame_layout = QVBoxLayout(preview_frame)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        preview_frame_layout.addWidget(self.preview_label)
        
        # Add details and preview to container
        preview_layout.addWidget(preview_frame, stretch=1)
        
        # Add widgets to splitter
        self.main_splitter.addWidget(screenshots_widget)
        self.main_splitter.addWidget(self.preview_container)
        
        # Add splitter to main layout
        self.main_layout.addWidget(header_widget)
        self.main_layout.addWidget(self.main_splitter)
        
        # Initially hide preview container
        self.preview_container.hide()
        
        # Create loading overlay
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()  # Ensure it starts hidden
        
        # Create full screen preview window
        self.full_screen_preview = FullScreenPreview()
        
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
        
        # Schedule screenshot loading
        QTimer.singleShot(100, lambda: self.populate_screenshots(self.load_screenshot_paths()))
        
        # Connect resize event
        self.preview_label.resizeEvent = self.on_preview_resize
        
        # Connect preview click event
        self.preview_label.mousePressEvent = self.on_preview_clicked
        
        self.load_preferences()
        
        # Initial sort after everything is initialized
        self.sort_game_tabs()
    
    def save_filename(self):
        if not self.current_screenshot:
            return
            
        new_name = self.filename_edit.text().strip()
        if not new_name:
            return
            
        # Validate filename
        invalid_chars = set('/\\:*?"<>|')
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        # Check for invalid characters
        if any(char in new_name for char in invalid_chars):
            toast = Toast(self)
            toast.show_message("Error: Filename cannot contain /\\:*?\"<>|")
            return
            
        # Check for reserved names
        base_name = os.path.splitext(new_name)[0].upper()
        if base_name in reserved_names:
            toast = Toast(self)
            toast.show_message("Error: Reserved system name (e.g., CON, PRN)")
            return
            
        # Check length limits
        if len(new_name) > 255:
            toast = Toast(self)
            toast.show_message("Error: Filename too long (max 255 chars)")
            return
        if len(new_name) < 3:
            toast = Toast(self)
            toast.show_message("Error: Filename too short (min 3 chars)")
            return
            
        # Check for trailing periods/spaces
        if new_name[-1] in ('.', ' '):
            toast = Toast(self)
            toast.show_message("Error: Filename cannot end with space or period")
            return
            
        try:
            dir_path = os.path.dirname(self.current_screenshot)
            new_path = os.path.join(dir_path, new_name)
            
            # If name hasn't changed
            if os.path.normpath(new_path) == os.path.normpath(self.current_screenshot):
                toast = Toast(self)
                toast.show_message("Filename saved")
                return
                
            # If file exists
            if os.path.exists(new_path):
                toast = Toast(self)
                toast.show_message("Filename saved (already exists)")
                return
                
            os.rename(self.current_screenshot, new_path)
            self.current_screenshot = new_path
            
            # Update item data
            current_item = self.list_widget.currentItem()
            if current_item:
                current_item.setData(Qt.ItemDataRole.UserRole, new_path)
                
                try:
                    game_id = new_path.split("remote\\")[1].split("\\")[0]
                    if game_id in self.game_tabs:
                        game_list = self.game_tabs[game_id]
                        for i in range(game_list.count()):
                            if game_list.item(i).data(Qt.ItemDataRole.UserRole) == self.current_screenshot:
                                game_list.item(i).setData(Qt.ItemDataRole.UserRole, new_path)
                                break
                except Exception:
                    pass
            
            toast = Toast(self)
            toast.show_message("Filename saved successfully!")
            
        except Exception as e:
            toast = Toast(self)
            toast.show_message(f"Error: {str(e)}")
    
    def open_file_location(self):
        if self.current_screenshot:
            subprocess.run(['explorer', '/select,', self.current_screenshot])
    
    def open_in_paint(self):
        if self.current_screenshot:
            subprocess.Popen(['mspaint', self.current_screenshot])
    
    def on_preview_resize(self, event):
        if self.current_screenshot:
            self.update_preview(self.current_screenshot)
        event.accept()
    
    def update_preview(self, screenshot_path):
        if not screenshot_path or not os.path.exists(screenshot_path):
            self.preview_label.clear()
            return
        
        try:
            pixmap = QPixmap(screenshot_path)
            if pixmap.isNull():
                raise Exception("Failed to load image")
            
            # Scale pixmap to fit within the frame while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled_pixmap)
            
            # Create fade-in animation
            fade_effect = QPropertyAnimation(self.preview_label, b"windowOpacity")
            fade_effect.setDuration(200)
            fade_effect.setStartValue(0.0)
            fade_effect.setEndValue(1.0)
            fade_effect.setEasingCurve(QEasingCurve.Type.OutCubic)
            fade_effect.start()
        except Exception as e:
            self.logger.error(f"Error updating preview: {e}")
            self.preview_label.setText("Preview unavailable")

    def on_screenshot_clicked(self, item):
        screenshot_path = item.data(Qt.ItemDataRole.UserRole)
        
        # If clicking the same item, unselect it
        if screenshot_path == self.current_screenshot:
            self.list_widget.clearSelection()
            self.preview_container.hide()
            self.current_screenshot = None
            return
        
        # Check if file still exists
        if not os.path.exists(screenshot_path):
            QMessageBox.warning(self, "File Not Found", 
                              "The screenshot file was not found. It may have been moved or deleted.")
            self.remove_missing_screenshot(item)
            return
        
        self.current_screenshot = screenshot_path
        
        if screenshot_path:
            self.logger.debug(f"Selected screenshot: {screenshot_path}")
            
            # Show preview container if hidden
            if not self.preview_container.isVisible():
                self.preview_container.show()
            
            # Update preview with animation
            self.update_preview(screenshot_path)
            
            # Update details
            try:
                # Get game name
                game_id = screenshot_path.split("remote\\")[1].split("\\")[0]
                game_name = self.game_db.get_game_name(game_id)
                self.update_game_name_display(game_id, game_name)
                
                # Update filename
                self.filename_edit.setText(os.path.basename(screenshot_path))
                
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
                self.logger.error(f"Error updating details: {e}")
        else:
            # Hide preview container if no screenshot is selected
            self.preview_container.hide()

    def refresh_screenshots(self):
        """Refresh the screenshots list"""
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            try:
                self.loading_overlay.show()
                self.list_widget.clear()
                # Clear game tabs except "All"
                while self.tab_widget.count() > 1:
                    self.tab_widget.removeTab(1)
                self.game_tabs.clear()
                self.populate_screenshots(self.load_screenshot_paths())
                
                # Apply both sorting methods after refresh
                self.sort_game_tabs()
                self.sort_screenshots()
            finally:
                self.loading_overlay.hide()

    def create_game_tab(self, game_id, game_name):
        """Create a new tab for a game with proper ID association"""
        DebugConsole.log(f"Creating tab for game_id: {game_id} - {game_name}")
        
        # Only truncate if the full name is longer than 25 characters
        display_name = game_name if len(game_name) <= 25 else f"{game_name[:25]}..."
        
        # Check if tab already exists for this game
        if game_id in self.game_tabs:
            DebugConsole.log(f"Tab already exists for {game_id}")
            return self.game_tabs[game_id]
            
        # Create new list widget for the game
        game_list = QListWidget()
        game_list.setViewMode(QListWidget.ViewMode.IconMode)
        game_list.setIconSize(QSize(200, 200))
        game_list.setSpacing(10)
        game_list.setMovement(QListWidget.Movement.Static)
        game_list.itemClicked.connect(self.on_screenshot_clicked)
        
        # Create container widget to hold the list
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(game_list)
        
        # Add tab and store reference
        tab_index = self.tab_widget.addTab(container, display_name)
        self.game_tabs[game_id] = game_list
        
        DebugConsole.log(f"Created tab at index {tab_index} for {game_id}")
        
        return game_list

    def populate_screenshots(self, screenshots):
        """Populate list widgets with screenshots"""
        DebugConsole.log(f"Populating {len(screenshots)} screenshots")
        
        # Show loading overlay with progress
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.show()
            self.loading_overlay.set_progress(0, len(screenshots))
            QApplication.processEvents()  # Force UI update
        
        for i, screenshot in enumerate(screenshots, 1):
            try:
                # Update progress
                if hasattr(self, 'loading_overlay'):
                    self.loading_overlay.set_progress(i, len(screenshots))
                
                # Extract game_id from path
                game_id = screenshot.split("remote\\")[1].split("\\")[0]
                
                # Create list item
                item = QListWidgetItem()
                pixmap = QPixmap(screenshot)
                icon = QIcon(pixmap)
                item.setIcon(icon)
                item.setData(Qt.ItemDataRole.UserRole, screenshot)
                self.list_widget.addItem(item)
                
                # Add to game tab
                game_list = self.create_game_tab(game_id, self.game_db.get_game_name(game_id))
                
                # Create item for game tab
                game_item = QListWidgetItem()
                game_item.setIcon(icon)
                game_item.setData(Qt.ItemDataRole.UserRole, screenshot)
                game_list.addItem(game_item)
            except Exception as e:
                self.logger.error(f"Error adding to game tab: {e}")
        
        self.status_label.setText(f"Found {len(screenshots)} screenshots")
        self.logger.debug(f"Loaded {len(screenshots)} screenshots")
        
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.close()
            
        # Trigger sorting after population is complete
        self.sort_game_tabs()
        self.sort_screenshots()

    def copy_image(self):
        if self.current_screenshot:
            clipboard = QGuiApplication.clipboard()
            pixmap = QPixmap(self.current_screenshot)
            clipboard.setPixmap(pixmap)
            
            # Show toast notification
            toast = Toast(self)
            toast.show_message("Image copied to clipboard!")

    def on_preview_clicked(self, event):
        if self.current_screenshot:
            self.full_screen_preview.show_image(self.current_screenshot)

    def edit_game_name(self):
        if not self.current_screenshot:
            return
            
        try:
            game_id = self.current_screenshot.split("remote\\")[1].split("\\")[0]
            current_name = self.game_db.get_game_name(game_id)
            
            editor = GameNameEditor(self)
            editor.name_input.setText(current_name.replace("Unknown Game (ID: ", "").replace(")", ""))
            
            def save_game_name():
                new_name = editor.name_input.text().strip()
                if new_name:
                    self.game_db.set_custom_game_name(game_id, new_name)
                    self.game_name_label.setText(new_name)
                    # Update tab name if it exists
                    if game_id in self.game_tabs:
                        tab_index = self.tab_widget.indexOf(self.game_tabs[game_id].parent())
                        if tab_index != -1:
                            self.tab_widget.setTabText(tab_index, new_name)
                    editor.close()
            
            editor.save_button.clicked.connect(save_game_name)
            editor.show()
            
        except Exception as e:
            self.logger.error(f"Error editing game name: {e}")

    def update_game_name_display(self, game_id, game_name):
        self.game_name_label.setText(game_name)
        # Show edit button if it's an unknown game
        self.edit_game_name_button.setVisible("Unknown Game" in game_name)

    def save_preferences(self):
        """Save game data to cache file"""
        try:
            cache_dir = os.path.join(os.getenv('APPDATA'), 'Game Screenshot Viewer')
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            with open(os.path.join(cache_dir, 'config.json'), 'w') as f:
                json.dump({
                    "game_sort_order": self.game_sort_combo.currentText(),
                    "screenshot_sort_order": self.screenshot_sort_combo.currentText()
                }, f)
        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")

    def load_preferences(self):
        """Load game data from cache file"""
        try:
            config_path = os.path.join(os.getenv('APPDATA'), 'Game Screenshot Viewer', 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                    # Set game sort order
                    game_sort = config.get("game_sort_order", "Newest")
                    index = self.game_sort_combo.findText(game_sort)
                    if index >= 0:
                        self.game_sort_combo.setCurrentIndex(index)
                    else:
                        self.game_sort_combo.setCurrentIndex(0)  # Default to Newest
                    
                    # Set screenshot sort order
                    screenshot_sort = config.get("screenshot_sort_order", "Newest")
                    index = self.screenshot_sort_combo.findText(screenshot_sort)
                    if index >= 0:
                        self.screenshot_sort_combo.setCurrentIndex(index)
                    else:
                        self.screenshot_sort_combo.setCurrentIndex(0)  # Default to Newest
        except Exception as e:
            # Use defaults if loading fails
            self.game_sort_combo.setCurrentIndex(0)  # Newest
            self.screenshot_sort_combo.setCurrentIndex(0)  # Newest
            self.logger.error(f"Error loading preferences: {e}")

    def closeEvent(self, event):
        self.save_preferences()
        super().closeEvent(event)

    def remove_missing_screenshot(self, item):
        """Remove a screenshot that no longer exists from the UI"""
        screenshot_path = item.data(Qt.ItemDataRole.UserRole)
        
        # Remove from main list
        row = self.list_widget.row(item)
        self.list_widget.takeItem(row)
        
        # Remove from game-specific tabs if it exists
        try:
            game_id = screenshot_path.split("remote\\")[1].split("\\")[0]
            if game_id in self.game_tabs:
                game_list = self.game_tabs[game_id]
                for i in range(game_list.count()):
                    if game_list.item(i).data(Qt.ItemDataRole.UserRole) == screenshot_path:
                        game_list.takeItem(i)
                        break
        except Exception as e:
            self.logger.error(f"Error removing missing screenshot from game tab: {e}")
        
        # Update status
        self.status_label.setText(f"Removed missing screenshot: {os.path.basename(screenshot_path)}")

    def start_missing_screenshots_check(self):
        """Start a timer to periodically check for missing screenshots"""
        self.missing_check_timer = QTimer(self)
        self.missing_check_timer.timeout.connect(self.check_for_missing_screenshots)
        self.missing_check_timer.start(30000)  # Check every 30 seconds

    def check_for_missing_screenshots(self):
        """Check all displayed screenshots still exist"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            screenshot_path = item.data(Qt.ItemDataRole.UserRole)
            if not os.path.exists(screenshot_path):
                self.remove_missing_screenshot(item)

    def get_sorted_screenshots(self, screenshots):
        sort_order = self.game_sort_combo.currentText()
        if sort_order == "Most Recent":
            return sorted(screenshots, key=lambda x: os.path.getmtime(x), reverse=True)
        elif sort_order == "A to Z":
            return sorted(screenshots, key=lambda x: x)
        elif sort_order == "Z to A":
            return sorted(screenshots, key=lambda x: x, reverse=True)
        elif sort_order == "Screenshot Count":
            return sorted(screenshots, key=lambda x: os.path.getsize(x), reverse=True)
        return screenshots

    def sort_game_tabs(self):
        """Sort the game tabs based on the current sort order"""
        if self.is_sorting:
            return
            
        self.is_sorting = True
        self.loading_overlay.show()
        try:
            DebugConsole.log("\n=== Starting tab sort operation ===")
            
            sort_order = self.game_sort_combo.currentText()
            DebugConsole.log(f"Sort order: {sort_order}")
            
            if self.tab_widget.count() <= 1:  # Only "All" tab exists
                DebugConsole.log("No game tabs to sort")
                return
            
            # Create a list of (game_id, tab_text, widget, screenshot_time) tuples
            tabs_info = []
            for game_id, game_list in self.game_tabs.items():
                newest_time = 0
                oldest_time = float('inf')
                # Find newest and oldest screenshot times for this game
                for i in range(game_list.count()):
                    screenshot_path = game_list.item(i).data(Qt.ItemDataRole.UserRole)
                    if os.path.exists(screenshot_path):
                        mtime = os.path.getmtime(screenshot_path)
                        if mtime > newest_time:
                            newest_time = mtime
                        if mtime < oldest_time:
                            oldest_time = mtime
                
                for i in range(1, self.tab_widget.count()):
                    if self.tab_widget.widget(i) == game_list.parent():
                        tabs_info.append((game_id, self.tab_widget.tabText(i), self.tab_widget.widget(i), newest_time, oldest_time))
                        break
            
            # Sort based on current sort order
            if sort_order == "A to Z":
                tabs_info.sort(key=lambda x: x[1].lower())
            elif sort_order == "Z to A":
                tabs_info.sort(key=lambda x: x[1].lower(), reverse=True)
            elif sort_order == "Newest":
                tabs_info.sort(key=lambda x: x[3], reverse=True)  # Sort by newest screenshot time
            elif sort_order == "Oldest":
                tabs_info.sort(key=lambda x: x[4])  # Sort by oldest screenshot time
            elif sort_order == "Screenshot Count":
                tabs_info.sort(key=lambda x: self.game_tabs[x[0]].count(), reverse=True)
            
            DebugConsole.log(f"Sorted tabs: {[tab[1] for tab in tabs_info]}")
            
            # Rebuild tabs in sorted order
            current_index = self.tab_widget.currentIndex()
            for i, (game_id, tab_text, widget, _, _) in enumerate(tabs_info, 1):
                current_tab_index = self.tab_widget.indexOf(widget)
                if current_tab_index != i:
                    self.tab_widget.tabBar().moveTab(current_tab_index, i)
            if current_index > 0:  # Restore selection if it was a game tab
                self.tab_widget.setCurrentIndex(current_index)
            
            DebugConsole.log("=== Tab sort operation completed ===\n")
            QApplication.processEvents()  # Force UI update
        finally:
            self.loading_overlay.hide()
            self.is_sorting = False

    def sort_list_widget(self, list_widget, sort_order):
        """Helper method to sort a QListWidget based on the specified order"""
        try:
            # Store the paths and text of all items
            items_data = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole):
                    items_data.append({
                        'path': item.data(Qt.ItemDataRole.UserRole),
                        'text': item.text(),
                        'icon': item.icon()
                    })
            
            # Get current selection to restore after sorting
            current_item = list_widget.currentItem()
            current_path = current_item.data(Qt.ItemDataRole.UserRole) if current_item else None
            
            # Sort based on the selected order
            if sort_order == "Newest":
                items_data.sort(key=lambda x: os.path.getmtime(x['path']) if os.path.exists(x['path']) else 0, reverse=True)
            elif sort_order == "Oldest":
                items_data.sort(key=lambda x: os.path.getmtime(x['path']) if os.path.exists(x['path']) else 0)
            elif sort_order == "A to Z":
                items_data.sort(key=lambda x: os.path.basename(x['path']).lower())
            elif sort_order == "Z to A":
                items_data.sort(key=lambda x: os.path.basename(x['path']).lower(), reverse=True)
            elif sort_order == "Largest":
                items_data.sort(key=lambda x: os.path.getsize(x['path']) if os.path.exists(x['path']) else 0, reverse=True)
            elif sort_order == "Smallest":
                items_data.sort(key=lambda x: os.path.getsize(x['path']) if os.path.exists(x['path']) else 0)
            
            # Clear and repopulate with new items
            list_widget.clear()
            for data in items_data:
                item = QListWidgetItem(data['icon'], data['text'])
                item.setData(Qt.ItemDataRole.UserRole, data['path'])
                list_widget.addItem(item)
                
            # Restore selection if it existed
            if current_path:
                for i in range(list_widget.count()):
                    if list_widget.item(i).data(Qt.ItemDataRole.UserRole) == current_path:
                        list_widget.setCurrentItem(list_widget.item(i))
                        break
        except Exception as e:
            DebugConsole.error(f"Error sorting list: {e}")
            raise

    def load_screenshot_paths(self):
        """Load and return all screenshot paths"""
        DebugConsole.log("Loading screenshot paths")
        try:
            # Get the default Steam screenshots path
            steam_path = os.path.expandvars(r"%ProgramFiles(x86)%\\Steam")
            userdata_path = os.path.join(steam_path, "userdata")
            
            if not os.path.exists(userdata_path):
                self.status_label.setText("Steam userdata folder not found!")
                return []
            
            # Find all screenshot folders
            screenshots = []
            for user_folder in os.listdir(userdata_path):
                screenshots_path = os.path.join(userdata_path, user_folder, "760", "remote", "*", "screenshots")
                screenshot_folders = glob.glob(screenshots_path)
                
                for folder in screenshot_folders:
                    screenshots.extend(glob.glob(os.path.join(folder, "*.jpg")))
                    screenshots.extend(glob.glob(os.path.join(folder, "*.png")))
            
            return screenshots
            
        except Exception as e:
            DebugConsole.error(f"Error loading screenshot paths: {e}")
            return []

    def sort_screenshots(self):
        """Sort screenshots in all lists based on the current sort order"""
        if self.is_sorting:
            return
            
        self.is_sorting = True
        self.loading_overlay.show()
        try:
            DebugConsole.log("\n=== Starting screenshot sort operation ===")
            
            sort_order = self.screenshot_sort_combo.currentText()
            DebugConsole.log(f"Screenshot sort order: {sort_order}")
            
            # Sort the main 'All' list
            self.sort_list_widget(self.list_widget, sort_order)
            
            # Sort all game-specific lists
            for game_list in self.game_tabs.values():
                self.sort_list_widget(game_list, sort_order)
            
            DebugConsole.log("=== Screenshot sort operation completed ===\n")
            QApplication.processEvents()  # Force UI update
        except Exception as e:
            DebugConsole.error(f"Error during screenshot sorting: {e}")
            QMessageBox.warning(self, "Sort Error", f"Failed to sort screenshots: {str(e)}")
        finally:
            self.loading_overlay.hide()
            self.is_sorting = False

# Simple main function similar to the working examples
app = QApplication(sys.argv)
app.setStyle('Fusion')  # Set Fusion style for better dark theme support
window = SteamScreenshotsViewer()
window.show()
sys.exit(app.exec()) 