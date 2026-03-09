@echo off
:: Chronos Gateway - Windows Service Uninstallation Script
:: Run as Administrator

echo ============================================
echo   Chronos Gateway - Uninstall
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

set "SERVICE_NAME=ChronosGateway"

:: Check if service exists
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    echo Service %SERVICE_NAME% is not installed.
    pause
    exit /b 0
)

:: Stop service
echo Stopping service...
net stop "%SERVICE_NAME%" >nul 2>&1

:: Delete service
echo Deleting service...
sc delete "%SERVICE_NAME%"

echo.
echo ============================================
echo   Uninstall Complete!
echo ============================================
echo.
echo The service has been removed.
echo Your config and logs have been preserved.
echo.

pause
