@echo off
pushd .
cd /D "%~dp0"

rem Clean up
rd /s /q dist > nul 2>&1
rd /s /q build > nul 2>&1

rem Build Qt ui/ts files
call make_qt.cmd

rem Build base bundle via pyinstaller
poetry run pyinstaller openfreebuds.spec

rem Build setup.exe
makensis openfreebuds.nsi

