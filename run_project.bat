@echo off
title LebEstates Web Server
echo ===================================================
echo Starting LebEstates Web Server (Anaconda Base Python)
echo ===================================================
echo.

:: Navigate to the folder where run.py is located
cd /d "%~dp0LebEstates"

:: Run the Flask server
C:\ProgramData\anaconda3\python.exe run.py

echo.
echo Server stopped.
pause
