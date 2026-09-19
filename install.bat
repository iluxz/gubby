@echo off
title gubby installer
color 0D

echo ========================================
echo         gubby installer v1.0
echo ========================================
echo.

:: check for python
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] python found
    python --version
    goto :install_deps
)

echo [!] python not found, downloading...
echo.

:: download python 3.12 installer
curl -L -o "%TEMP%\python-installer.exe" "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
if %errorlevel% neq 0 (
    echo [X] failed to download python. install manually from https://python.org
    pause
    exit /b 1
)

echo [*] installing python (this may take a minute)...
"%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0
if %errorlevel% neq 0 (
    echo [X] python install failed. try running as admin.
    pause
    exit /b 1
)

echo [OK] python installed. restarting terminal...
set PATH=%PATH%;C:\Python312\;C:\Python312\Scripts\
timeout /t 2 >nul

:install_deps
echo.
echo [*] installing required libraries...
echo.

python -m pip install --upgrade pip >nul 2>&1
python -m pip install PyQt6 qrcode[pil] Pillow
if %errorlevel% neq 0 (
    echo [X] failed to install some libraries
    pause
    exit /b 1
)

echo.
echo ========================================
echo    all done! launching gubby...
echo ========================================
echo.

start "" python "%~dp0gubby.py"
