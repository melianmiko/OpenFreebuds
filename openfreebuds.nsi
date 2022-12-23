!include "MUI2.nsh"
!include "x64.nsh"

!define APP_NAME "OpenFreebuds"
!define APP_DEVELOPER "MelianMiko"
!define APP_BUILD_NAME "openfreebuds"
!define APP_EXE "openfreebuds.exe"
!define REG_KEY

Name "${APP_NAME}"
OutFile "dist\${APP_BUILD_NAME}.install.exe"
Unicode True
AutoCloseWindow True

;Default installation folder
InstallDir "$PROGRAMFILES64\${APP_DEVELOPER}\${APP_NAME}"

;Get installation folder from registry if available
InstallDirRegKey HKCU "Software\${APP_DEVELOPER} ${APP_NAME}" ""

;Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------
;Interface Settings

	!define MUI_ABORTWARNING

;--------------------------------
;Pages

	!insertmacro MUI_PAGE_DIRECTORY
	!insertmacro MUI_PAGE_INSTFILES

	!insertmacro MUI_UNPAGE_CONFIRM
	!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

	!insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "Dummy Section" SecDummy

    ; Kill running process
    nsExec::ExecToStack "C:\Windows\System32\taskkill.exe /f /im:openfreebuds.exe"

	; Copy files
	SetOutPath "$INSTDIR"
	File /r "dist\${APP_BUILD_NAME}\"

	;Shortcuts
	CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
	CreateShortCut "$SMPROGRAMS\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"

	;Store installation folder
	WriteRegStr HKCU "Software\${APP_DEVELOPER} ${APP_NAME}" "" $INSTDIR
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP" \
			"DisplayName" "OpenFreebuds"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP" \
			"UninstallString" "$\"$INSTDIR\uninstall.exe$\""

	;Create uninstaller
	WriteUninstaller "$INSTDIR\Uninstall.exe"

	;Run app
	Exec '"$WINDIR\explorer.exe" "$INSTDIR\${APP_EXE}"'

SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"

    ; Kill running process
    nsExec::ExecToStack "C:\Windows\System32\taskkill.exe /f /im:openfreebuds.exe"

	; Delete all
	Delete "$INSTDIR\Uninstall.exe"
	Delete "$DESKTOP\${APP_NAME}.lnk"
	Delete "$SMPROGRAMS\${APP_NAME}.lnk"
	RMDir /r "$INSTDIR"

	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP"
	DeleteRegKey /ifempty HKCU "Software\${APP_DEVELOPER} ${APP_NAME}"

SectionEnd
