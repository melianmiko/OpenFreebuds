#!/usr/bin/env bash
PATH=/usr/lib/qt6/bin:$PATH

cd "$(dirname "$0")"/../openfreebuds_qt

for ts_file in ./assets/i18n/*.ts
do
  [ -f "$ts_file" ] || break

  pylupdate6 \
    --no-obsolete \
    --exclude scripts \
    --exclude debian \
    --ts $ts_file .
done
