#!/usr/bin/env bash

cd "$(dirname "$0")"

rm ../../dist/*
rm openfreebuds*

make prepare

dpkg-buildpackage -S
dpkg-buildpackage -b

mv ../openfreebuds_* .
