DESTDIR="/"

PYSTRAY_VERSION="0.19.2"

all: builddir/openfreebuds/pystray
	cp -r src/* builddir/openfreebuds

builddir/openfreebuds/pystray:
	mkdir -p builddir/openfreebuds/openfreebuds
	pip install --target=builddir/openfreebuds --no-deps pystray==${PYSTRAY_VERSION}

install:
	rm -rf /opt/openfreebuds
	cp -r builddir/openfreebuds ${DESTDIR}/opt/openfreebuds
	cp tools/linux_entrypoint.py ${DESTDIR}/usr/bin/openfreebuds

start:
	# Start app without compilation
	PYTHONPATH=""${PWD}/src"" python3 src/ofb_launcher.py --verbose
