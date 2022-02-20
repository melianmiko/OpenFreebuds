@echo off

set PYTHONPATH=%CD%

if not exist builddir mkdir builddir
cd builddir

pyinstaller ..\bin\openfreebuds
xcopy ..\openfreebuds_assets\ .\dist\openfreebuds\openfreebuds_assets\ /s /e

cd ..

