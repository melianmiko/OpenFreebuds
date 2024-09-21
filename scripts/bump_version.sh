#!/usr/bin/env bash

if [[ "$1" == "" ]]
then
  echo "Usage: ./scripts/bump_version.sh [new_version_tag]"
  exit 1
fi

# Init
cd "$(dirname "$0")"/..
source scripts/constants.sh

# Init tools
[ ! -d ./scripts/tools ] && mkdir ./scripts/tools
[ ! -f ./scripts/tools/flatpak-pip-generator ] && \
  echo "Downloading flatpak-pip-generator tool..." && \
  wget https://github.com/flatpak/flatpak-builder-tools/raw/refs/heads/master/pip/flatpak-pip-generator && \
  chmod +x flatpak-pip-generator

# Bump python wheel version
VERSION_SHORT=`echo $1 | cut -d . -f -2`
sed -bi "s/^version =.*/version = \"$VERSION_SHORT\"/g" pyproject.toml

# Create ./openfreebuds_qt/version_info.py
echo "VERSION = '$1'" > ./openfreebuds_qt/version_info.py
echo "LIBRARIES = [" >> ./openfreebuds_qt/version_info.py
poetry export --without-hashes -n --with extras | sed 's/\r$//' | while read line
do
  echo "    '$line'," >> ./openfreebuds_qt/version_info.py
done
echo "]" >> ./openfreebuds_qt/version_info.py

# Create flatpak PyPI manifests
poetry export \
  --without no_flatpak,dev \
  --without-hashes \
  -o ./scripts/build_flatpak/requirements.txt
sed -i '/sys_platform == \"darwin\"/d' ./scripts/build_flatpak/requirements.txt
sed -i '/sys_platform == \"win32\"/d' ./scripts/build_flatpak/requirements.txt
sed -i 's/ and python_version < \"3.11\"//g' ./scripts/build_flatpak/requirements.txt
./scripts/tools/flatpak-pip-generator \
  -r ./scripts/build_flatpak/requirements.txt \
  -o ./scripts/build_flatpak/python3-requirements.json

# Update nsis vars
sed -bi "s/!define APP_VERSION.*/!define APP_VERSION \"$1\"/g" scripts/build_win32/openfreebuds.nsi

# Update debian pkg changelog
prev_changelog=`cat scripts/build_debian/debian/changelog`
echo "openfreebuds ($1-1) $DEB_CODENAMES; urgency=medium

  * Changelog isn't provided

 -- $DEVELOPER_SIGN  $(date -R)

$prev_changelog" > scripts/build_debian/debian/changelog
