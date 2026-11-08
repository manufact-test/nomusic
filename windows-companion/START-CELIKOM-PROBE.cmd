@echo off
setlocal
cd /d "%~dp0"
set "REPORT=%~dp0CELIKOM-Windows-report.txt"
"%~dp0CELIKOM-Windows-Probe.exe" > "%REPORT%" 2>&1
if not exist "%REPORT%" (
  echo Report could not be saved. Extract ZIP to your Downloads folder first.
  pause
  exit /b 1
)
start "" notepad.exe "%REPORT%"
echo CELIKOM report saved next to this script.
echo You can share CELIKOM-Windows-report.txt in your ChatGPT project.
pause
