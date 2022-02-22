# This Makefile should be used only for Linux building
# For Windows build, use make_win32.cmd file

start:
	# Start app without compilation
	PYTHONPATH=${PWD} python3 bin/openfreebuds --verbose

all:
	mkdir -p builddir
	cd builddir && PYTHONPATH=${PWD} nuitka3 \
		         --follow-imports \
			 --include-package=pynput \
			 --include-package=Xlib \
		         ../bin/openfreebuds
	cd builddir && upx openfreebuds.bin

install:
	cp builddir/openfreebuds.bin /usr/bin/openfreebuds
	cp -r openfreebuds_assets /usr/share/openfreebuds
