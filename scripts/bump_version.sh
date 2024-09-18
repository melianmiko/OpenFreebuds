#!/usr/bin/env bash

if [[ "$1" == "" ]]
then
  echo "Usage: ./scripts/bump_version.sh [new_version_tag]"
  exit 1
fi

cd "$(dirname "$0")"/..
source scripts/constants.sh

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

# Update nsis vars
sed -bi "s/!define APP_VERSION.*/!define APP_VERSION \"$1\"/g" scripts/build_win32/openfreebuds.nsi

# Update debian pkg changelog
prev_changelog=`cat scripts/build_debian/debian/changelog`
echo "openfreebuds ($1-1) $DEB_CODENAMES; urgency=medium

  * Changelog isn't provided

 -- $DEVELOPER_SIGN  $(date -R)

$prev_changelog" > scripts/build_debian/debian/changelog
