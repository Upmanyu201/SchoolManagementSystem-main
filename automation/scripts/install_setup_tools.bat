@echo off
title Install Setup Tools
color 0B

echo.
echo ========================================
echo   Installing Setup Tools
echo ========================================
echo.
echo This will install additional dependencies
echo required for the setup and management tools.
echo.
echo Dependencies to install:
echo   - psutil (System monitoring)
echo   - qrcode (QR code generation)
echo   - requests (Update checking)
echo   - colorama (Colored output)
echo   - tqdm (Progress bars)
echo.
pause

cd /d "%~dp0\..\..\"

echo.
echo Checking for virtual environment...
if exist "venv\Scripts\python.exe" (
    echo Virtual environment found!
    echo.
    echo Installing dependencies...
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r automation\requirements_setup.txt
) else (
    echo Virtual environment not found.
    echo.
    echo Installing to system Python...
    python -m pip install --upgrade pip
    python -m pip install -r automation\requirements_setup.txt
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo You can now use all setup and management tools.
echo.
echo Next steps:
echo   1. Run automation\scripts\setup_wizard.bat for first-time setup
echo   2. Or run start.bat for the main menu
echo.
pause
