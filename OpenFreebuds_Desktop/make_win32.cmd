@echo off

pip install -r requirements.txt
pip install -r requirements_win32.txt

pyinstaller bin/openfreebuds
