@echo off
pushd .
cd /D "%~dp0"

For %%i in ("%CD%\..\..\openfreebuds_qt\assets\i18n\*.ts")do lrelease %%~i
poetry run pyuic6 ..\..\openfreebuds_qt\designer

popd .
