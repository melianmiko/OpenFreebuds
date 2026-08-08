!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"

!define APP_NAME "OpenFreebuds"
!define APP_VERSION "0.18.0"
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
	ClearErrors
	ReadRegStr $0 HKCU "Software\${APP_DEVELOPER} ${APP_NAME}" ""
	${If} ${Errors}
		CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
		CreateShortCut "$SMPROGRAMS\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
	${EndIf}

	;Store installation folder
	WriteRegStr HKCU "Software\${APP_DEVELOPER} ${APP_NAME}" "" $INSTDIR
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP" \
			"DisplayIcon" "$INSTDIR\openfreebuds.exe"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP" \
			"DisplayName" "OpenFreebuds"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP" \
			"DisplayVersion" "${APP_VERSION}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP" \ 
			"QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP" \
			"UninstallString" "$\"$INSTDIR\uninstall.exe$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP" \
			"Publisher" "${APP_DEVELOPER}"

	; Bundle size
	${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
	IntFmt $0 "0x%08X" $0
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}_APP" \
			"EstimatedSize" "$0"

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
	DeleteRegKey HKCU "Software\${APP_DEVELOPER} ${APP_NAME}"

SectionEnd
