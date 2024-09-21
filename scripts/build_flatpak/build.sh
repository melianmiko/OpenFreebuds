#!/usr/bin/env bash

cd "$(dirname "$0")"/../..

rm -rf scripts/build_flatpak/release
./scripts/make_qt_parts.sh
poetry build

cd scripts/build_flatpak
flatpak-builder \
	--force-clean \
	--user \
	--install-deps-from=flathub \
	--repo=repo \
	--install builddir \
	pw.mmk.OpenFreebuds.yml
