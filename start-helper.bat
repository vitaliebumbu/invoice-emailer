@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
  echo Setup has not been completed yet.
  echo Double-click install.bat first.
  echo.
  pause
  exit /b 1
)

echo Starting Invoice Emailer helper...
echo Keep this window open while using Acadia.
echo.
"%~dp0venv\Scripts\python.exe" app.py
pause
