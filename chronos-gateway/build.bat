@echo off
:: ============================================
::   Chronos Gateway - Build Script
::   Builds PyInstaller and NSIS Installer
:: ============================================

echo ============================================
echo   Chronos Gateway - Build Script
echo ============================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: This script should be run as Administrator
    echo for proper installation of Windows Service.
    echo.
)

:: Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: ============================================
:: STEP 1: Build with PyInstaller
:: ============================================
echo [1/3] Building with PyInstaller...
echo.

if not exist "dist" (
    echo Running PyInstaller...
    pyinstaller chronos-gateway.spec --clean
    if %errorlevel% neq 0 (
        echo ERROR: PyInstaller failed!
        pause
        exit /b 1
    )
) else (
    echo Skipping PyInstaller (dist folder exists)
)

:: Check if PyInstaller output exists
if not exist "dist\ChronosGateway\ChronosGateway.exe" (
    echo ERROR: PyInstaller did not create the executable!
    echo Expected: dist\ChronosGateway\ChronosGateway.exe
    pause
    exit /b 1
)

echo PyInstaller build successful!

:: ============================================
:: STEP 2: Copy config example
:: ============================================
echo.
echo [2/3] Preparing files...
echo.

if not exist "dist\ChronosGateway\config.yaml.example" (
    copy config.yaml.example dist\ChronosGateway\ >nul
)

:: ============================================
:: STEP 3: Build NSIS Installer
:: ============================================
echo.
echo [3/3] Building NSIS Installer...
echo.

:: Check if NSIS is installed
where makensis >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: NSIS is not installed!
    echo.
    echo To install NSIS:
    echo 1. Download from: https://nsis.sourceforge.io/Download
    echo 2. Install and add to PATH
    echo 3. Run this script again
    echo.
    echo For now, you can run the executable directly from:
    echo   dist\ChronosGateway\ChronosGateway.exe
    echo.
    pause
    exit /b 0
)

:: Build installer
makensis install.nsi
if %errorlevel% neq 0 (
    echo ERROR: NSIS failed!
    pause
    exit /b 1
)

:: ============================================
:: DONE
:: ============================================
echo.
echo ============================================
echo   BUILD COMPLETE!
echo ============================================
echo.
echo Output files:
echo   - dist\ChronosGateway\ChronosGateway.exe
echo   - ChronosGatewaySetup.exe
echo.
echo To install:
echo   1. Run ChronosGatewaySetup.exe as Administrator
echo   2. Edit config.yaml with your backend settings
echo   3. Run install.bat to install Windows Service
echo.

pause
