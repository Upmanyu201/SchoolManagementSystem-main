@echo off
chcp 65001 >nul
title School Management System - Smart Launcher

:: Change to project root directory
cd /d "%~dp0.."

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo [INFO] Please run: python -m venv venv
    pause
    exit /b 1
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Check if manage.py exists
if not exist "manage.py" (
    echo [ERROR] manage.py not found! Please run from Django project root.
    pause
    exit /b 1
)

:: Install required packages if not present
echo [INFO] Checking dependencies...
python -c "import psutil" 2>nul || (
    echo [INFO] Installing psutil...
    pip install psutil
)

:: Check for production mode argument
set PRODUCTION_MODE=false
if "%1"=="--production" set PRODUCTION_MODE=true
if "%1"=="-p" set PRODUCTION_MODE=true

:: Set environment variables for production
if "%PRODUCTION_MODE%"=="true" (
    echo [INFO] Starting in PRODUCTION mode...
    set PRODUCTION=true
    set DEBUG=False
) else (
    echo [INFO] Starting in DEVELOPMENT mode...
    set PRODUCTION=false
)

:: Run the Python startup script
echo [INFO] Starting School Management System...
python ImpScripts\enhanced_start_server.py

pause