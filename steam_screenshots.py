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
                            QSplitter, QTabWidget, QFrame, QProgressBar)
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
        self.games = {}
        self.custom_games = {}
        self.pending_updates = set()  # Track new game IDs for batch updates
        self.cache_file = os.path.join(os.path.dirname(__file__), 'steam_games_cache.json')
        self.custom_cache_file = os.path.join(os.path.dirname(__file__), 'custom_games_cache.json')
        self.load_cache()
        self.load_custom_cache()

    def load_cache(self):
        """Load game data from cache file"""
        try:
            if os.path.exists(self.cache_file):
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

    def load_custom_cache(self):
        """Load custom game names from cache file"""
        try:
            if os.path.exists(self.custom_cache_file):
                with open(self.custom_cache_file, 'r', encoding='utf-8') as f:
                    self.custom_games = json.load(f)
        except Exception as e:
            print(f"Error loading custom cache: {e}")

    def save_custom_cache(self):
        """Save custom game names to cache file"""
        try:
            with open(self.custom_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_games, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving custom cache: {e}")

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
            print(f"Error updating database (working offline): {e}")
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
            print(f"Error processing pending updates (working offline): {e}")

    def get_game_name(self, app_id):
        """Get game name from app ID"""
        app_id = str(app_id)
        
        # Check custom names first
        if app_id in self.custom_games:
            return self.custom_games[app_id]
        
        # Check main database
        if app_id in self.games:
            return self.games[app_id]
        
        # Queue for update if not found
        self.queue_update_for_id(app_id)
        
        return f"Unknown Game (ID: {app_id})"

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

class SteamScreenshotsViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing main window...")
        
        # Set dark theme for window
        set_window_theme(self)
        
        # Initialize game database
        self.game_db = SteamGameDatabase()
        self.game_tabs = {}
        self.current_screenshot = None
        
        # Basic window setup
        self.setWindowTitle("Steam Screenshots Viewer")
        self.resize(1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create header with status and refresh button
        header_widget = QWidget()
        header_widget.setFixedHeight(40)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.status_label = QLabel("Loading...")
        self.status_label.setStyleSheet("color: white; font-size: 14px;")
        header_layout.addWidget(self.status_label)
        
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.setFixedSize(24, 24)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2a475e;
                color: #c7d5e0;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #66c0f4;
                color: #1b2838;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_screenshots)
        header_layout.addWidget(self.refresh_button)
        header_layout.addStretch()
        
        self.main_layout.addWidget(header_widget)
        
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
        
        # Details area
        self.details_widget = QWidget()
        self.details_widget.setFixedWidth(250)
        details_layout = QVBoxLayout(self.details_widget)
        
        # Game name
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
        self.edit_game_name_button.hide()  # Initially hidden
        
        game_name_layout.addWidget(self.game_name_label)
        game_name_layout.addWidget(self.edit_game_name_button)
        details_layout.addWidget(game_name_widget)
        
        # Filename edit section
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
        details_layout.addWidget(filename_widget)
        
        # File details
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #c7d5e0; padding: 5px;")
        details_layout.addWidget(self.date_label)
        
        self.resolution_label = QLabel()
        self.resolution_label.setStyleSheet("color: #c7d5e0; padding: 5px;")
        details_layout.addWidget(self.resolution_label)
        
        self.file_size_label = QLabel()
        self.file_size_label.setStyleSheet("color: #c7d5e0; padding: 5px;")
        details_layout.addWidget(self.file_size_label)
        
        # Action buttons
        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setSpacing(5)
        
        button_style = """
            QPushButton {
                background-color: #2a475e;
                color: #c7d5e0;
                border: none;
                border-radius: 3px;
                padding: 8px;
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
        actions_layout.addWidget(self.open_location_button)
        
        self.copy_path_button = QPushButton("📋 Copy Image")
        self.copy_path_button.setStyleSheet(button_style)
        self.copy_path_button.clicked.connect(self.copy_image)
        actions_layout.addWidget(self.copy_path_button)
        
        self.open_paint_button = QPushButton("🎨 Open in Paint")
        self.open_paint_button.setStyleSheet(button_style)
        self.open_paint_button.clicked.connect(self.open_in_paint)
        actions_layout.addWidget(self.open_paint_button)
        
        details_layout.addWidget(actions_widget)
        details_layout.addStretch()
        
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
        
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.preview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_scroll.setWidget(self.preview_label)
        
        preview_frame_layout.addWidget(self.preview_scroll)
        
        # Add details and preview to container
        preview_layout.addWidget(self.details_widget)
        preview_layout.addWidget(preview_frame, stretch=1)
        
        # Add widgets to splitter
        self.main_splitter.addWidget(screenshots_widget)
        self.main_splitter.addWidget(self.preview_container)
        
        # Add splitter to main layout
        self.main_layout.addWidget(self.main_splitter)
        
        # Initially hide preview container
        self.preview_container.hide()
        
        # Create loading overlay
        self.loading_overlay = LoadingOverlay(self)
        
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
        QTimer.singleShot(100, self.load_screenshots)
        
        # Connect resize event
        self.preview_scroll.resizeEvent = self.on_preview_resize
        
        # Connect preview click event
        self.preview_label.mousePressEvent = self.on_preview_clicked
    
    def save_filename(self):
        if not self.current_screenshot:
            return
            
        new_name = self.filename_edit.text()
        if not new_name:
            return
            
        try:
            dir_path = os.path.dirname(self.current_screenshot)
            new_path = os.path.join(dir_path, new_name)
            
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "A file with this name already exists.")
                return
                
            os.rename(self.current_screenshot, new_path)
            self.current_screenshot = new_path
            self.refresh_screenshots()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to rename file: {str(e)}")
    
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
        if not screenshot_path:
            return
            
        pixmap = QPixmap(screenshot_path)
        scaled_pixmap = pixmap.scaled(
            self.preview_scroll.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Create fade-in animation
        self.preview_label.setPixmap(scaled_pixmap)
        fade_effect = QPropertyAnimation(self.preview_label, b"windowOpacity")
        fade_effect.setDuration(200)
        fade_effect.setStartValue(0.0)
        fade_effect.setEndValue(1.0)
        fade_effect.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade_effect.start()

    def on_screenshot_clicked(self, item):
        screenshot_path = item.data(Qt.ItemDataRole.UserRole)
        
        # If clicking the same item, unselect it
        if screenshot_path == self.current_screenshot:
            self.list_widget.clearSelection()
            self.preview_container.hide()
            self.current_screenshot = None
            return
            
        self.current_screenshot = screenshot_path
        
        if screenshot_path:
            print(f"Selected screenshot: {screenshot_path}")
            
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
                print(f"Error updating details: {e}")
        else:
            # Hide preview container if no screenshot is selected
            self.preview_container.hide()

    def refresh_screenshots(self):
        """Refresh the screenshots list"""
        self.loading_overlay.show()
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

    def load_screenshots(self):
        print("Loading screenshots...")
        self.loading_overlay.show()
        self.loading_overlay.set_progress(0, 0)  # Reset progress
        
        try:
            # Get the default Steam screenshots path
            steam_path = os.path.expandvars(r"%ProgramFiles(x86)%\Steam")
            userdata_path = os.path.join(steam_path, "userdata")
            
            if not os.path.exists(userdata_path):
                self.status_label.setText("Steam userdata folder not found!")
                self.loading_overlay.close()
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
                self.loading_overlay.close()
                return
            
            # Sort screenshots by modification time (newest first)
            screenshots.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            total_screenshots = len(screenshots)
            
            # Add screenshots to the list and game tabs
            for i, screenshot in enumerate(screenshots, 1):
                # Update progress
                self.loading_overlay.set_progress(i, total_screenshots)
                QApplication.processEvents()  # Keep UI responsive
                
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
            self.loading_overlay.close()

    def copy_image(self):
        if self.current_screenshot:
            clipboard = QGuiApplication.clipboard()
            pixmap = QPixmap(self.current_screenshot)
            clipboard.setPixmap(pixmap)
    
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
            print(f"Error editing game name: {e}")

    def update_game_name_display(self, game_id, game_name):
        self.game_name_label.setText(game_name)
        # Show edit button if it's an unknown game
        self.edit_game_name_button.setVisible("Unknown Game" in game_name)

# Simple main function similar to the working examples
app = QApplication(sys.argv)
app.setStyle('Fusion')  # Set Fusion style for better dark theme support
window = SteamScreenshotsViewer()
window.show()
sys.exit(app.exec()) 