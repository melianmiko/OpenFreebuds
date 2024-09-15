#!/usr/bin/env bash

cd "$(dirname "$0")"

dpkg-buildpackage -S
dpkg-buildpackage -b

mv ../*.deb .
mv ../*.buildinfo .
mv ../*.changes .

