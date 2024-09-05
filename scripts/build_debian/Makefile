DESTDIR := ${PWD}/dist

DIST_PACKAGES_PATH := /usr/lib/python3/dist-packages
WHEEL_FILE := $(shell find ${PWD} -maxdepth 1 -name '*.whl')

all:
	cd ../.. && pyuic6 openfreebuds_qt/designer
	cd ../.. && /usr/lib/qt6/bin/lrelease openfreebuds_qt/assets//i18n
	cd ../.. && poetry build
	cp ../../dist/openfreebuds* .

install:
	pip install --no-dependencies --target="${DESTDIR}${DIST_PACKAGES_PATH}" ${WHEEL_FILE}
	mkdir -p ${DESTDIR}/usr/bin
	mv ${DESTDIR}${DIST_PACKAGES_PATH}/bin/* ${DESTDIR}/usr/bin/
	rm -rf ${DESTDIR}${DIST_PACKAGES_PATH}/bin
	mkdir -p ${DESTDIR}/usr/share/applications
	cp ../openfreebuds.desktop ${DESTDIR}/usr/share/applications

clean:
	rm -rf dist *.tar.gz *.whl
