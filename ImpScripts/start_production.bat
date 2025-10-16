@echo off
chcp 65001 >nul
title School Management System - Production Mode

echo ========================================
echo   PRODUCTION MODE STARTUP
echo ========================================
echo.

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

:: Set production environment variables
set PRODUCTION=true
set DEBUG=False
set DJANGO_SETTINGS_MODULE=config.settings

echo [INFO] Starting in PRODUCTION mode...
echo [WARN] Debug mode is DISABLED
echo [INFO] Static files will be served efficiently
echo.

:: Run the Python startup script with production mode
python ImpScripts\start_server.py

pause