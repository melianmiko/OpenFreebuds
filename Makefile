DESTDIR=

PYBLUEZ_COMMIT=07ebef044195331a48bbb90a3acb911922048ba0
PYBLUEZ_OUT_FILE=PyBluez-0.30-cp310-cp310-linux_x86_64.whl

all: lib/mtrayapp lib/pynput lib/sv_ttk lib/bluetooth
	# Copy all contents to builddir
	rm -rf builddir/openfreebuds
	mkdir -p builddir/openfreebuds
	cp -r src/* builddir/openfreebuds
	cp -r lib/* builddir/openfreebuds

	# Wipe cache
	find builddir/openfreebuds -type d -name "__pycache__" -exec rm -rf {} +

lib/mtrayapp lib/pynput lib/sv_ttk:
	mkdir -p lib

	# Fetch libraries that will be packaged into deb-file
	# (i know that this isn't a "Linux-way", but this is easier than
	# package all of them by myself)
	cd lib && pip install --target=. --no-deps mtrayapp==1.0.2 pynput~=1.7.6 sv-ttk==2.2

lib/bluetooth:
	mkdir -p lib/tmp

	# Fetch pybluez edge and build a wheel
	[ -x lib/tmp/pybluez ] && rm -rf lib/tmp/pybluez
	git clone https://github.com/pybluez/pybluez.git lib/tmp/pybluez
	cd lib/tmp/pybluez && git checkout -q ${PYBLUEZ_COMMIT}
	cd lib/tmp/pybluez && python3 setup.py bdist_wheel

	# Install to lib dir
	cd lib && pip install --target=. --no-deps tmp/pybluez/dist/${PYBLUEZ_OUT_FILE}

	rm -rf lib/tmp

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
	PYTHONPATH="${PWD}/src:${PWD}/lib" python3 src/ofb_launcher.py --verbose

shell:
	# Start app without compilation
	PYTHONPATH="${PWD}/src:${PWD}/lib" python3 src/ofb_launcher.py --verbose --shell


