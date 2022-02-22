# This Makefile should be used only for Linux building
# For Windows build, use make_win32.cmd file
DESTDIR=/

all:
	mkdir -p builddir
	cd builddir && PYTHONPATH=${PWD} nuitka3 \
		         --follow-imports \
		         --nofollow-import-to=Xlib \
		         --nofollow-import-to=evdev \
		         --nofollow-import-to=winsdk \
		         ../bin/openfreebuds
	cd builddir && upx openfreebuds.bin

install:
	cp builddir/openfreebuds.bin ${DESTDIR}/usr/bin/openfreebuds
	cp bin/openfreebuds-command ${DESTDIR}/usr/bin
	cp -r openfreebuds_assets ${DESTDIR}/usr/share/openfreebuds

start:
	# Start app without compilation
	PYTHONPATH=${PWD} python3 bin/openfreebuds --verbose
