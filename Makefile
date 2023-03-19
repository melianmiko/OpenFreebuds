DESTDIR=

all: lib/pystray lib/pynput lib/sv_ttk
	# Copy all contents to builddir
	rm -rf builddir/openfreebuds
	mkdir -p builddir/openfreebuds
	cp -r src/* builddir/openfreebuds
	cp -r lib/* builddir/openfreebuds

	# Wipe cache
	find builddir/openfreebuds -type d -name "__pycache__" -exec rm -rf {} +

lib/pystray lib/pynput lib/sv_ttk:
	mkdir -p lib

	# Fetch libraries that will be packaged into deb-file
	# (i know that this isn't a "Linux-way", but this is easier than
	# package all of them by myself)
	cd lib && pip install --target=. --no-deps -r ../requirements-pkg.txt

install:
	rm -rf ${DESTDIR}/opt/openfreebuds
	mkdir -p ${DESTDIR}/opt
	cp -r builddir/openfreebuds ${DESTDIR}/opt/openfreebuds
	mkdir -p ${DESTDIR}/usr/bin
	mkdir -p ${DESTDIR}/usr/share/applications
	cp src/linux_entrypoint.py ${DESTDIR}/usr/bin/openfreebuds
	cp docs/openfreebuds.desktop ${DESTDIR}/usr/share/applications
