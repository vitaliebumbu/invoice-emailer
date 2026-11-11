@echo off
rem Restarts the Invoice Emailer helper so it picks up new code (after git pull).
rem Stops only this folder's helper (python / pythonw from this venv), then starts it hidden again.
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$venv = (Join-Path '%~dp0' 'venv').ToLower(); Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^pythonw?\.exe$' -and $_.ExecutablePath -and $_.ExecutablePath.ToLower().StartsWith($venv) } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; 'Stopped old helper (PID ' + $_.ProcessId + ')' }"

timeout /t 1 /nobreak >nul
wscript.exe "%~dp0start-helper-hidden.vbs"
echo Invoice helper restarted.
timeout /t 3 >nul
