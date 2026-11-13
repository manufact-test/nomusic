@echo off
setlocal
where adb >nul 2>&1
if errorlevel 1 (
  echo ADB not found. Install Android Platform Tools and add adb to PATH.
  pause
  exit /b 1
)
adb get-state >nul 2>&1
if errorlevel 1 (
  echo Phone not connected or USB debugging is not authorized.
  pause
  exit /b 1
)
set "OUT=%~dp0CELIKOM-A1-Audio-Diagnostics.txt"
echo Capturing only CELIKOM A1 diagnostic event markers.
echo Open the CELIKOM A1 test clone, play one track, test pause/seek/Next.
echo Press Ctrl+C here when finished. Output: "%OUT%"
adb logcat -v brief -s CELIKOM_A1_EXIT_WITNESS:I | findstr /c:"event=" > "%OUT%"
echo.
echo Diagnostic capture stopped. File: "%OUT%"
pause
