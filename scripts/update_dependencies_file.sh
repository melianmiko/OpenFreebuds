#!/usr/bin/env bash
cd "$(dirname "$0")"
poetry export --without-hashes -n > ../openfreebuds_qt/assets/dependencies.txt
