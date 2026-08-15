@echo off
title Stop Netflix Login Link App
echo Dang tat server tren port 5000...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a
)

echo Da tat.
timeout /t 2 /nobreak >nul
