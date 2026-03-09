; Chronos Gateway NSIS Installer Script
; Build: makensis install.nsi

; ===================
; INCLUDE FILES
; ===================
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"

; ===================
; GENERAL SETTINGS
; ===================
Name "Chronos Gateway"
OutFile "ChronosGatewaySetup.exe"
InstallDir "$PROGRAMFILES64\Chronos Gateway"
InstallDirRegKey HKLM "Software\ChronosGateway" "InstallDir"
RequestExecutionLevel admin

; ===================
; VERSION INFO
; ===================
!define VERSION "1.0.0"
!define COMPANY "Chronos"
!define PRODUCT_NAME "Chronos Gateway"
!define EXE_NAME "ChronosGateway.exe"

VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=1033 "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey /LANG=1033 "CompanyName" "${COMPANY}"
VIAddVersionKey /LANG=1033 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1033 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=1033 "FileDescription" "Chronos Gateway - Access Control System"

; ===================
; INTERFACE SETTINGS
; ===================
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; ===================
; PAGES
; ===================
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ===================
; LANGUAGES
; ===================
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Bulgarian"

; ===================
; INSTALL SECTION
; ===================
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Copy all files from dist folder
    File /r "dist\ChronosGateway\*.*"
    
    ; Copy config example
    File "config.yaml.example"
    
    ; Create directories
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\data"
    
    ; Copy NSSM if not exists
    ; Note: NSSM will be downloaded by install.bat or included in the package
    
    ; ===================
    ; CREATE SHORTCUTS
    ; ===================
    CreateDirectory "$SMPROGRAMS\Chronos Gateway"
    CreateShortcut "$SMPROGRAMS\Chronos Gateway\Chronos Gateway.lnk" "$INSTDIR\${EXE_NAME}"
    CreateShortcut "$SMPROGRAMS\Chronos Gateway\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    CreateShortcut "$DESKTOP\Chronos Gateway.lnk" "$INSTDIR\${EXE_NAME}"
    
    ; ===================
    ; WRITE REGISTRY KEYS
    ; ===================
    WriteRegStr HKLM "Software\ChronosGateway" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\ChronosGateway" "Version" "${VERSION}"
    
    ; ===================
    ; WRITE UNINSTALL INFO
    ; ===================
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChronosGateway" "DisplayName" "Chronos Gateway"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChronosGateway" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChronosGateway" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChronosGateway" "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChronosGateway" "Publisher" "${COMPANY}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChronosGateway" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChronosGateway" "NoRepair" 1
    
    ; Get install size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChronosGateway" "EstimatedSize" "$0"
    
    ; ===================
    ; CREATE UNINSTALLER
    ; ===================
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; ===================
    ; START SERVICE (Optional - handled by install.bat)
    ; ===================
    ; Don't start service automatically - let user do it manually
    
SectionEnd

; ===================
; UNINSTALL SECTION
; ===================
Section "Uninstall"
    ; Stop service
    nsExec::ExecToLog 'net stop ChronosGateway'
    nsExec::ExecToLog 'sc delete ChronosGateway'
    
    ; Remove files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\Chronos Gateway.lnk"
    RMDir /r "$SMPROGRAMS\Chronos Gateway"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\ChronosGateway"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChronosGateway"
    
    ; Note: User data in %APPDATA%\ChronosGateway can be optionally removed
    ; Uncomment below to remove user data
    ; RMDir /r "$APPDATA\ChronosGateway"
    
SectionEnd
