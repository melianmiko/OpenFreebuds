@echo off

rem Clean up
rd /s /q dist > nul 2>&1
rd /s /q build > nul 2>&1

rem Build Qt ui files
poetry run pyuic6 ..\..\openfreebuds_qt\designer

rem Build base bundle via pyinstaller
poetry run pyinstaller openfreebuds.spec

rem Build setup.exe
makensis openfreebuds.nsi
