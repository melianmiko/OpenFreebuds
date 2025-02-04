@echo off
pushd .
cd /D "%~dp0"

rem Clean up
rd /s /q dist > nul 2>&1
rd /s /q build > nul 2>&1

rem Build Qt ui/ts files
call make_qt.cmd

rem Build portable via pyinstaller
poetry run pyinstaller openfreebuds_portable.spec

rem Rename release files
python rename_release.py
