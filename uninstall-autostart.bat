@echo off
setlocal

set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Invoice Emailer Helper.lnk"

if exist "%SHORTCUT%" (
  del "%SHORTCUT%"
  echo Removed Invoice Emailer helper from Windows startup.
) else (
  echo Invoice Emailer helper was not found in Windows startup.
)

echo.
pause
