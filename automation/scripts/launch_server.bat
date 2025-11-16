@echo off
title School Management System - Server
color 0A

echo.
echo ========================================
echo   School Management System
echo   Starting Server...
echo ========================================
echo.

cd /d "%~dp0\..\..\"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe automation\server\launch_server.py
) else (
    python automation\server\launch_server.py
)

pause
