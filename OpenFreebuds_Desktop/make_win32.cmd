@echo off

set PYTHONPATH=%CD%

if not exist builddir mkdir builddir
if exist builddir\dist rd /s /q builddir/dist

cd builddir

pyinstaller --windowed ..\bin\openfreebuds
xcopy ..\openfreebuds_assets\ .\dist\openfreebuds\openfreebuds_assets\ /s /e

cd ..
