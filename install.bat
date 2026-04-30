@echo off
setlocal
cd /d "%~dp0"

echo.
echo Invoice Emailer setup
echo =====================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_CMD=python"
  ) else (
    echo Python was not found.
    echo Install Python from https://www.python.org/downloads/windows/
    echo Make sure "Add python.exe to PATH" is checked during install.
    echo.
    pause
    exit /b 1
  )
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env from .env.example.
)

if not exist "venv\Scripts\python.exe" (
  echo Creating local Python environment...
  %PYTHON_CMD% -m venv venv
  if %errorlevel% neq 0 (
    echo Failed to create the Python environment.
    pause
    exit /b 1
  )
)

echo Installing required packages...
"%~dp0venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo Failed to install required packages.
  pause
  exit /b 1
)

echo Setting helper to start automatically with Windows...
call "%~dp0install-autostart.bat" /quiet
if %errorlevel% neq 0 (
  echo Failed to set up automatic start.
  echo You can still double-click start-helper.bat before using Acadia.
)

echo.
echo Setup complete.
echo.
echo Next:
echo 1. Open .env and confirm JOBS_ROOT and FROM_NAME.
echo 2. In Chrome, load the extension folder from this project.
echo 3. Open Acadia and use Invoice Request.
echo.
pause
