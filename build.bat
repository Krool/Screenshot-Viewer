@echo off
echo Building Game Screenshot Viewer...

REM Kill any running instances
taskkill /F /IM "Game Screenshot Viewer.exe" 2>NUL

REM Clean up previous build
rmdir /S /Q "build" 2>NUL
rmdir /S /Q "dist" 2>NUL

REM Create and activate virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM Install requirements
pip install -r requirements.txt

REM Build executable using spec file
pyinstaller --noconfirm --clean "Game Screenshot Viewer.spec"

REM Create ZIP archive
cd dist
powershell -Command "Compress-Archive -Path '.\Game Screenshot Viewer\*' -DestinationPath 'Game_Screenshot_Viewer.zip' -Force"
cd ..

echo Build complete! The executable is in "dist\Game Screenshot Viewer" folder
echo A ZIP archive has been created at "dist\Game_Screenshot_Viewer.zip"
pause 