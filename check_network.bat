@echo off
title Network Status Checker
color 0E

:LOOP
cls
echo.
echo ========================================
echo   🌐 Network Status Monitor
echo ========================================
echo.

:: Get current timestamp
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATE=%%a/%%b/%%c
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME=%%a:%%b
echo 🕒 Last updated: %DATE% %TIME%

echo.
echo 📡 Network Interfaces:

:: Check Wi-Fi
set WIFI_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"Wireless LAN adapter Wi-Fi" /A:1 ^| findstr "IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do set WIFI_IP=%%b
)
if defined WIFI_IP (
    set WIFI_IP=%WIFI_IP: =%
    echo    ✅ Wi-Fi: %WIFI_IP%
    echo       🌐 Access: http://%WIFI_IP%:8000/
) else (
    echo    ❌ Wi-Fi: Not connected
)

:: Check Mobile Hotspot
set HOTSPOT_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"Local Area Connection\*" /A:5 ^| findstr "IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        if not defined HOTSPOT_IP set HOTSPOT_IP=%%b
    )
)
if defined HOTSPOT_IP (
    set HOTSPOT_IP=%HOTSPOT_IP: =%
    echo    ✅ Mobile Hotspot: %HOTSPOT_IP%
    echo       📱 Access: http://%HOTSPOT_IP%:8000/
) else (
    echo    ❌ Mobile Hotspot: Not active
)

echo.
echo 🖥️  Local Access: http://127.0.0.1:8000/

echo.
echo 🔄 Auto-refreshing every 5 seconds...
echo 💡 Press Ctrl+C to exit
echo.

timeout /t 5 >nul
goto LOOP