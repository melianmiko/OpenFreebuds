# This Makefile shuld be used only for Linux building
# For Windows build, use make_win32.cmd file

all:
	PYTHONPATH=${PWD} nuitka3 \
		   --follow-imports \
		   bin/openfreebuds
	upx openfreebuds.bin

