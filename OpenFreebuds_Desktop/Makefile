# This Makefile shuld be used only for Linux building
# For Windows build, use make_win32.cmd file

all:
	mkdir -p builddir
	cd builddir && PYTHONPATH=${PWD} nuitka3 \
		         --follow-imports \
		         ../bin/openfreebuds
	cd builddir && upx openfreebuds.bin

install:
	cp builddir/openfreebuds.bin /usr/bin/openfreebuds
	cp -r openfreebuds_assets /usr/share/openfreebuds
