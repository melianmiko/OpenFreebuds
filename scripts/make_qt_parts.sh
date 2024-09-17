#!/usr/bin/env bash
cd "$(dirname "$0")"/..

poetry run pyuic6 openfreebuds_qt/designer
/usr/lib/qt6/bin/lrelease openfreebuds_qt/assets/i18n/*.ts
