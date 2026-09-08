@echo off
title LebEstates Web Server
echo ===================================================
echo Starting LebEstates Web Server (.venv)
echo ===================================================
echo.

:: Navigate to the folder where run.py is located
cd /d "%~dp0LebEstates"

:: Run the Flask server
"%~dp0LebEstates\.venv\Scripts\python.exe" run.py

echo.
echo Server stopped.
pause
