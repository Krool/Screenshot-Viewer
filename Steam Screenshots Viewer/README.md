# Steam Screenshots Viewer

A modern, user-friendly application to view and manage your Steam screenshots.

## Features

- View all your Steam screenshots in a grid layout
- Sort screenshots by date (newest first)
- View full-size images with zoom functionality
- Rename screenshots directly from the app
- Quick access to screenshot locations
- Dark theme matching Steam's aesthetic
- Automatic refresh to find new screenshots

## Installation

### Option 1: Run the Executable (Recommended)

1. Download the "Steam Screenshots Viewer.zip" file
2. Extract the ZIP file to any location
3. Run "Steam Screenshots Viewer.exe"

### Option 2: Run from Source

If you prefer to run from source, you'll need Python 3.8 or higher:

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python steam_screenshots.py
```

## Usage

1. Launch the application
2. Your Steam screenshots will automatically be loaded and displayed
3. Click any thumbnail to view the full image
4. Click the image to toggle between fit-to-window and full-size view
5. Use the rename feature to change screenshot names
6. Click the folder icon to open the screenshot's location
7. Use the refresh button to scan for new screenshots

## Notes

- The application looks for screenshots in the default Steam installation directory
- If your Steam is installed in a non-standard location, you may need to modify the source code
- Screenshots are automatically sorted by date, with the newest appearing first

## Building from Source

To create your own executable:

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Run the build script:
```bash
build.bat
```

The executable will be created in the "Steam Screenshots Viewer" folder. 