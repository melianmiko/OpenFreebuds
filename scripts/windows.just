winget_install := "winget install -e --no-upgrade --id"

# Make windows portable & installer
[group("windows"),windows]
win32: win32_installer win32_portable

# Make windows installer
[group("windows"),windows]
win32_installer: win32_bundle
    New-Item -ItemType Directory -Force -Path ./dist
    cd ./scripts; & "C:\Program Files (x86)\NSIS\Bin\makensis.exe" openfreebuds.nsi
    mv -Force ./scripts/dist/openfreebuds.install.exe ./dist/openfreebuds_{{version}}_win32.exe

# Make windows portable executable
[group("windows"),windows]
win32_portable:
    New-Item -ItemType Directory -Force -Path ./dist
    cd ./scripts; & pdm run pyinstaller -y openfreebuds_portable.spec
    mv -Force ./scripts/dist/openfreebuds_portable.exe ./dist/openfreebuds_{{version}}_win32_portable.exe

# Prepare ./dist/ for win32 installer build
[group("windows"),windows,private]
win32_bundle:
    cd ./scripts; pdm run pyinstaller -y openfreebuds.spec

# Install base project dependencies through WinGet
[group("windows"),windows]
deps_winget:
    -{{ winget_install }} Casey.Just
    -{{ winget_install }} NSIS.NSIS
    -{{ winget_install }} UPX.UPX
    -{{ winget_install }} Python.Python.3.14
    -{{ winget_install }} Microsoft.VisualStudio.2022.BuildTools --override "--passive --wait --add Microsoft.VisualStudio.Workload.VCTools;includeRecommended"
    -powershell -ExecutionPolicy ByPass -c "irm https://pdm-project.org/install-pdm.py | python -"
