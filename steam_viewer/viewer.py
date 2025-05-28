"""
Steam Screenshots Viewer main window implementation.
"""

import os
import datetime
import glob
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QListWidget,
                            QLabel, QScrollArea, QListWidgetItem, QPushButton,
                            QHBoxLayout, QLineEdit, QMessageBox, QSplitter)
from PyQt6.QtGui import QPixmap, QIcon, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QPoint, pyqtProperty, QApplication

from .spinner import LoadingSpinner

class SteamScreenshotsViewer(QMainWindow):
    # Common Steam game IDs
    STEAM_GAME_IDS = {
        "570": "Dota 2",
        "730": "Counter-Strike 2",
        "440": "Team Fortress 2",
        "1091500": "Cyberpunk 2077",
        "1174180": "Red Dead Redemption 2",
        "1245620": "Elden Ring",
        "292030": "The Witcher 3: Wild Hunt",
        "271590": "Grand Theft Auto V",
        "1599340": "Lost Ark",
        "578080": "PUBG: BATTLEGROUNDS",
        "252490": "Rust",
        "359550": "Rainbow Six Siege",
        "230410": "Warframe",
        "238960": "Path of Exile",
        "1172470": "Apex Legends",
        "346110": "ARK: Survival Evolved",
        "1063730": "New World",
        "1449850": "Baldur's Gate 3",
        "582010": "Monster Hunter: World",
        "1085660": "Destiny 2",
        "431960": "Wallpaper Engine",
        "1811260": "EA SPORTS FC™ 24",
        "1086940": "Baldur's Gate 3",
        "105600": "Terraria",
        "218620": "PAYDAY 2",
        "236390": "War Thunder",
        "227300": "Euro Truck Simulator 2",
        "1938090": "Call of Duty®",
        "1517290": "Hogwarts Legacy",
        "2357570": "The Finals",
        "1240440": "Halo Infinite",
        "1551360": "Forza Horizon 5",
        "1203220": "NARAKA: BLADEPOINT",
        "1794680": "Lethal Company",
        "648800": "Raft",
        "739630": "Phasmophobia",
        "1222670": "The Planet Crafter",
        "892970": "Valheim",
        "1716740": "Starfield",
        "281990": "Stellaris",
        "394360": "Hearts of Iron IV",
        "435150": "Divinity: Original Sin 2",
        "1145360": "Hades",
        "1462040": "7 Days to Die",
        "289070": "Sid Meier's Civilization VI",
        "1506830": "FIFA 23",
        "1599340": "Lost Ark",
        "322330": "Don't Starve Together",
        "550": "Left 4 Dead 2",
        "252950": "Rocket League",
        "304930": "Unturned",
        "242760": "The Forest",
        "620": "Portal 2",
        "4000": "Garry's Mod",
        "381210": "Dead by Daylight",
        "1172620": "Sea of Thieves",
        "1222670": "The Planet Crafter",
        "1158310": "Crusader Kings III",
        "1904540": "Sons Of The Forest"
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Screenshots Viewer")
        
        # Set initial size to 60% of primary screen
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.6)
        height = int(screen.height() * 0.6)
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)
        
        # Allow resizing while keeping frameless
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # For resizing
        self.setMouseTracking(True)
        self.resize_edge = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        self.resize_border = 8  # Increased border width for easier grabbing
        
        # Initialize state variables
        self.zoomed = False
        self._selection_opacity = 0.5
        self.list_widget = None
        self.drag_position = None
        self.current_screenshot = None
        self.current_pixmap = None
        self.zoom_click_pos = None
        
        # Setup selection animation
        self.selection_animation = QPropertyAnimation(self, b"selection_opacity")
        self.selection_animation.setDuration(1000)
        self.selection_animation.setLoopCount(-1)  # Infinite loop
        self.selection_animation.setStartValue(0.5)
        self.selection_animation.setEndValue(1.0)
        
        # Set dark theme
        self.setup_theme()
        
        # Create central widget with border
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background-color: #1b2838;
                border: 1px solid #2a475e;
            }
        """)
        self.setCentralWidget(central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)  # Reduce spacing
        
        # Add title bar
        self.setup_title_bar()
        
        # Create splitter for dynamic resizing
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2a475e;
                height: 2px;
            }
        """)
        self.main_layout.addWidget(self.splitter)
        
        # Create and add list widget
        self.list_widget = self.setup_list_widget()
        self.splitter.addWidget(self.list_widget)
        
        # Create details and image container
        self.details_image_container = QWidget()
        self.details_image_container.hide()  # Hide initially
        self.details_layout = QVBoxLayout(self.details_image_container)
        self.details_layout.setContentsMargins(10, 10, 10, 10)
        self.details_layout.setSpacing(10)
        
        # Setup details panel
        self.setup_details_panel()
        
        # Setup image view
        self.setup_image_view()
        
        # Add to splitter
        self.splitter.addWidget(self.details_image_container)
        
        # Set initial splitter sizes (list takes all space when no selection)
        self.splitter.setSizes([1000, 0])
        
        # Load screenshots
        self.load_screenshots()

    # Copy all the remaining methods from the SteamScreenshotsViewer class here
    // ... paste all the methods ... 