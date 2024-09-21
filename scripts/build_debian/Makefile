DESTDIR := ${PWD}/dist

DIST_PACKAGES_PATH := /usr/lib/python3/dist-packages
WHEEL_FILE := $(shell find ${PWD} -maxdepth 1 -name '*.whl')

all:
	bash ../make_qt_parts.sh
	cd ../.. && poetry build
	cp ../../dist/openfreebuds* .

install:
	pip install --upgrade --no-dependencies --target="${DESTDIR}${DIST_PACKAGES_PATH}" ${WHEEL_FILE}
	mkdir -p ${DESTDIR}/usr/bin
	mv ${DESTDIR}${DIST_PACKAGES_PATH}/bin/* ${DESTDIR}/usr/bin/
	sed -i '1 s/^.*$$/\#\!\/usr\/bin\/env python3/' ${DESTDIR}/usr/bin/*
	rm -rf ${DESTDIR}${DIST_PACKAGES_PATH}/bin
	mkdir -p ${DESTDIR}/usr/share/icons/hicolor/256x256/apps
	install -Dm644 ./pw.mmk.OpenFreebuds.png ${DESTDIR}/usr/share/icons/hicolor/256x256/apps/pw.mmk.OpenFreebuds.png
	mkdir -p ${DESTDIR}/usr/share/applications
	install -Dm644 ./pw.mmk.OpenFreebuds.desktop ${DESTDIR}/usr//share/applications/pw.mmk.OpenFreebuds.desktop

clean:
	rm -rf dist *.tar.gz *.whl
