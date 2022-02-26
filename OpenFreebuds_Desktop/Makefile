# This Makefile should be used only for Linux building
# For Windows build, use make_win32.cmd file
DESTDIR=/

all:
	python make.py

install:
	cp builddir/openfreebuds.bin ${DESTDIR}/usr/bin/openfreebuds
	cp -r openfreebuds_assets ${DESTDIR}/usr/share/openfreebuds

start:
	# Start app without compilation
	PYTHONPATH=${PWD} python3 bin/openfreebuds --verbose
