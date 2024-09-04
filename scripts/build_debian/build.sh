#!/usr/bin/env bash
dpkg-buildpackage -S
dpkg-buildpackage -b

mv ../*.deb .
mv ../*.buildinfo .
mv ../*.changes .

