DESTDIR=/

all: builddir/openfreebuds/pystray
	python tools/mk_version_info.py
	cp -r src/* builddir/openfreebuds

builddir/openfreebuds/pystray:
	mkdir -p builddir/openfreebuds/openfreebuds
	pip install --target=builddir/openfreebuds --no-deps pystray==0.19.2

install:
	rm -rf /opt/openfreebuds
	cp -r builddir/openfreebuds /opt/openfreebuds
	cp tools/linux_entrypoint.py /usr/bin/openfreebuds

start:
	# Start app without compilation
	PYTHONPATH=""${PWD}/src"" python3 src/main.py --verbose
