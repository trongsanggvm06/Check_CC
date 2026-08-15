@echo off
title Netflix Login Link App
cd /d "%~dp0"

echo ==============================================
echo   Netflix Login Link Generator
echo ==============================================
echo.
echo Server: http://localhost:5000
echo (Browser se tu mo sau 3 giay)
echo.
echo An Ctrl+C de tat server.
echo ==============================================
echo.

REM Tat server cu dang chiem port 5000 (neu co)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Mo browser sau 3 giay (chay nen)
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:5000"

REM Chay Flask
python app.py

echo.
echo Server da dung. An phim bat ky de dong cua so.
pause >nul
