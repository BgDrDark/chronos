@echo off
:: Chronos Gateway - Windows Service Installation Script
:: Run as Administrator

echo ============================================
echo   Chronos Gateway - Installation
echo ============================================
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click on this file and select "Run as administrator"
    pause
    exit /b 1
)

:: Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Check if NSSM is available, download if not
set "NSSM_DIR=%SCRIPT_DIR%\nssm"
if not exist "%NSSM_DIR%\nssm.exe" (
    echo Downloading NSSM (Non-Sucking Service Manager)...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%TEMP%\nssm.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm' -Force"
    xcopy /E /Q "%TEMP%\nssm\nssm-2.24\win64\*" "%NSSM_DIR%\" >nul
    del /f /q "%TEMP%\nssm.zip"
    rmdir /s /q "%TEMP%\nssm"
    echo NSSM downloaded.
)

:: Set service name
set "SERVICE_NAME=ChronosGateway"
set "EXE_PATH=%SCRIPT_DIR%\ChronosGateway\ChronosGateway.exe"

:: Check if executable exists
if not exist "%EXE_PATH%" (
    echo ERROR: ChronosGateway.exe not found!
    echo Please ensure you have built the Gateway with PyInstaller first.
    echo Run: pyinstaller chronos-gateway.spec
    pause
    exit /b 1
)

:: Stop service if already running
echo Stopping existing service...
net stop "%SERVICE_NAME%" >nul 2>&1
sc delete "%SERVICE_NAME%" >nul 2>&1

:: Install service
echo Installing service...
"%NSSM_DIR%\nssm.exe" install "%SERVICE_NAME%" "%EXE_PATH%"

:: Configure service
echo Configuring service...
"%NSSM_DIR%\nssm.exe" set "%SERVICE_NAME%" AppDirectory "%SCRIPT_DIR%\ChronosGateway"
"%NSSM_DIR%\nssm.exe" set "%SERVICE_NAME%" DisplayName "Chronos Gateway Service"
"%NSSM_DIR%\nssm.exe" set "%SERVICE_NAME%" Description "Chronos Access Control Gateway - manages SR201 relays and RFID readers"
"%NSSM_DIR%\nssm.exe" set "%SERVICE_NAME%" Start SERVICE_AUTO_START
"%NSSM_DIR%\nssm.exe" set "%SERVICE_NAME%" AppRestartDelay 5000
"%NSSM_DIR%\nssm.exe" set "%SERVICE_NAME%" AppExitDefault 0
"%NSSM_DIR%\nssm.exe" set "%SERVICE_NAME%" AppStopMethodConsole 0 1500
"%NSSM_DIR%\nssm.exe" set "%SERVICE_NAME%" AppStopMethodWindow 0 1500

:: Set startup type
sc config "%SERVICE_NAME%" start= auto

:: Create logs directory
if not exist "%SCRIPT_DIR%\logs" mkdir "%SCRIPT_DIR%\logs"

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo Service Name: %SERVICE_NAME%
echo Executable: %EXE_PATH%
echo.
echo To start the service, run:
echo   net start %SERVICE_NAME%
echo.
echo To manage the service, use:
echo   Services ^> Chronos Gateway
echo.
echo To view logs, check:
echo   %SCRIPT_DIR%\logs\gateway.log
echo.

pause
