#!/usr/bin/env bash

cd "$(dirname "$0")"/..

# Compile wheel
./scripts/install.py build

# Build & install flatpak
cd scripts/build_flatpak
flatpak-builder \
	--force-clean \
	--user \
	--install-deps-from=flathub \
	--repo=repo \
	--install builddir \
	pw.mmk.OpenFreebuds.yml
