@echo off
title WebAI-to-API Server
cd /d "%~dp0WebAI-to-API"
echo ===================================================
echo   Starting WebAI-to-API Server on Port 6969...
echo ===================================================
py src\run.py --port 6969
if %errorlevel% neq 0 (
    echo.
    echo Trying with python command...
    python src\run.py --port 6969
)
pause
