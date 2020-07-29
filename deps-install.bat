@echo off
title Dependencies Install Script

REM This script attempts to ensure that any dependent libraries are installed.
echo.
echo Checking for Python...
call :CheckPython || call :InstallFailed "Could not find a valid Python binary!"
echo Installing pip...
call :InstallPip || call :InstallFailed "Could not find or install pip!"
echo Installing libraries...
call :InstallDeps || call :InstallFailed "Could not install libraries with pip!"
echo Install successful.
echo.
pause
exit 0

REM Makes sure python is installed and is version 3+.
:CheckPython
python.exe -c "import sys;assert sys.version_info >= (3, 0, 0)" >nul 2>&1 || exit /B 1
exit /B 0

REM Makes sure python v3 and basic utils are installed.
:InstallPip
python.exe -m ensurepip --default-pip >nul 2>&1 || exit /B 1
pip3.exe install --upgrade pip setuptools wheel >nul 2>&1 || exit /B 1
exit /B 0

REM Install dependency libraries.
:InstallDeps
pip3.exe install --upgrade pyautogui >nul 2>&1 || exit /B 1
pip3.exe install --upgrade pytesseract >nul 2>&1 || exit /B 1
pip3.exe install --upgrade pynput >nul 2>&1 || exit /B 1
pip3.exe install --upgrade opencv-python >nul 2>&1 || exit /B 1
exit /B 0

REM Prints error message before exiting with fail status.
:InstallFailed
echo Error: %~1
echo Install failed.
echo Make sure that python.exe and pip3.exe are in the system PATH variable.
echo.
pause
exit 1
