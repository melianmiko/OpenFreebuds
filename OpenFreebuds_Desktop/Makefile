DESTDIR=

all: lib
	rm -rf builddir/openfreebuds
	mkdir -p builddir/openfreebuds
	cp -r src/* builddir/openfreebuds
	cp -r lib/* builddir/openfreebuds
	find builddir/openfreebuds -type d -name "__pycache__" -exec rm -rf {} +

lib: src/openfreebuds_assets/ttk_theme
	mkdir -p lib
	cd lib && pip install --target=. --no-deps -r ../requirements_lib.txt

src/openfreebuds_assets/ttk_theme:
	mkdir -p src/openfreebuds_assets
	wget -O src/openfreebuds_assets/theme.zip https://github.com/rdbende/Sun-Valley-ttk-theme/archive/refs/heads/master.zip
	cd src/openfreebuds_assets && unzip theme.zip
	cd src/openfreebuds_assets && mv Sun-Valley-ttk-theme-master ttk_theme
	cd src/openfreebuds_assets && rm theme.zip

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


