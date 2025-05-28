@echo off
echo Building Steam Screenshots Viewer...

REM Kill any running instances
taskkill /F /IM "Steam Screenshots Viewer.exe" 2>NUL

REM Clean up previous build
rmdir /S /Q "build" 2>NUL
rmdir /S /Q "dist" 2>NUL

REM Create and activate virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM Install requirements
pip install -r requirements.txt

REM Build executable using spec file
pyinstaller --noconfirm --clean "Steam Screenshots Viewer.spec"

REM Create ZIP archive
cd dist
powershell -Command "Compress-Archive -Path '.\Steam Screenshots Viewer\*' -DestinationPath 'Steam_Screenshots_Viewer.zip' -Force"
cd ..

echo Build complete! The executable is in "dist\Steam Screenshots Viewer" folder
echo A ZIP archive has been created at "dist\Steam_Screenshots_Viewer.zip"
pause 