@echo off
title School Management System - Update Checker
color 0B

cd /d "%~dp0\..\..\"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe automation\updates\update_checker.py
) else (
    python automation\updates\update_checker.py
)

pause
