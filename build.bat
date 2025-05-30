@echo off
setlocal

:: Clean previous builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

:: Build using SPEC file (no additional flags needed)
pyinstaller --noconfirm --clean "game_screenshots.spec"

:: Verify and copy files
if exist "dist\Game Screenshot Viewer.exe" (
    mkdir "dist\Game Screenshot Viewer" 2>nul
    move "dist\Game Screenshot Viewer.exe" "dist\Game Screenshot Viewer\"
    copy "steam_games_cache.json" "dist\Game Screenshot Viewer\"
    copy "custom_games_cache.json" "dist\Game Screenshot Viewer\"
    copy "app_icon.ico" "dist\Game Screenshot Viewer\"
    echo Build SUCCESSFUL!
) else (
    echo Build FAILED - check PyInstaller logs in build\game_screenshots\warn-game_screenshots.txt
)

pause 