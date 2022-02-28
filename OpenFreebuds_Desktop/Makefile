DESTDIR="/"

all: lib builddir/openfreebuds/pystray
	cp -r src/* builddir/openfreebuds
	find builddir/openfreebuds -type d -name "__pycache__" -exec rm -rf {} +

lib:
	mkdir -p lib
	cd lib && pip wheel --no-deps pystray==0.19.2

builddir/openfreebuds/pystray:
	mkdir -p builddir/openfreebuds/openfreebuds
	pip install --target=builddir/openfreebuds --no-deps lib/*

install:
	rm -rf ${DESTDIR}/opt/openfreebuds
	mkdir -p ${DESTDIR}/opt
	cp -r builddir/openfreebuds ${DESTDIR}/opt/openfreebuds
	mkdir -p ${DESTDIR}/usr/bin
	mkdir -p ${DESTDIR}/usr/share/applications
	cp tools/linux_entrypoint.py ${DESTDIR}/usr/bin/openfreebuds
	cp tools/openfreebuds.desktop ${DESTDIR}/usr/share/applications

start:
	# Start app without compilation
	PYTHONPATH=""${PWD}/src"" python3 src/ofb_launcher.py --verbose
