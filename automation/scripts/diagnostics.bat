@echo off
title School Management System - Diagnostics
color 0E

cd /d "%~dp0\..\..\"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe automation\setup\diagnostics.py
) else (
    python automation\setup\diagnostics.py
)

pause
