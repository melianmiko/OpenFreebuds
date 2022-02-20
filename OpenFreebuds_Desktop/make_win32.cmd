@echo off

set PYTHONPATH=%CD%

if not exist builddir mkdir builddir
cd builddir
xcopy ..\openfreebuds_assets\ .\dist\openfreebuds\openfreebuds_assets\ /s /e

pyinstaller ..\bin\openfreebuds

cd ..

