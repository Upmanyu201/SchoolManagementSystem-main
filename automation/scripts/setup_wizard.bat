@echo off
title School Management System - Setup Wizard
color 0B

echo.
echo ========================================
echo   School Management System
echo   Setup Wizard
echo ========================================
echo.

cd /d "%~dp0\..\..\"

if exist "venv\Scripts\python.exe" (
    echo Using virtual environment...
    venv\Scripts\python.exe automation\setup\setup_wizard.py
) else (
    echo Using system Python...
    python automation\setup\setup_wizard.py
)

echo.
pause
