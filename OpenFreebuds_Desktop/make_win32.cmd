@echo off

set PYTHONPATH=%CD%

if not exist builddir mkdir builddir
cd builddir

pyinstaller ..\bin\openfreebuds

cd ..

