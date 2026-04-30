@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\pythonw.exe" (
  echo Setup has not been completed yet.
  echo Double-click install.bat first.
  echo.
  pause
  exit /b 1
)

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP%\Invoice Emailer Helper.lnk"
set "TARGET=%~dp0start-helper-hidden.vbs"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$shell = New-Object -ComObject WScript.Shell; $shortcut = $shell.CreateShortcut('%SHORTCUT%'); $shortcut.TargetPath = '%TARGET%'; $shortcut.WorkingDirectory = '%~dp0'; $shortcut.Description = 'Starts the Invoice Emailer local helper'; $shortcut.Save()"

echo.
echo Invoice Emailer helper will now start automatically when Windows starts.
echo.
echo Starting it now...
wscript.exe "%~dp0start-helper-hidden.vbs"
echo Done.
echo.
pause
