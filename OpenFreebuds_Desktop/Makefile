DESTDIR=

all:
	cp -r src/* builddir/openfreebuds
	find builddir/openfreebuds -type d -name "__pycache__" -exec rm -rf {} +

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

shell:
	# Start app without compilation
	PYTHONPATH=""${PWD}/src"" python3 src/ofb_launcher.py --verbose --shell


