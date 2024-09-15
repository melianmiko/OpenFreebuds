#!/usr/bin/env bash
PATH=/usr/lib/qt6/bin:$PATH

cd "$(dirname "$0")"/../openfreebuds_qt

# Sync base ts-file
echo "-- Base locale update"
pylupdate6 --no-obsolete --ts ./assets/i18n/en.ts .

# Sync new *.po-files
for po_file in ./assets/i18n/*.po
do
  [ -f "$po_file" ] || break
  locale=`basename ${po_file%.*}`
  if ! [ -f ./assets/i18n/$locale.ts ]
  then
    echo "-- Import $locale from PO-file"
    lconvert ./assets/i18n/$locale.po -o ./assets/i18n/$locale.ts
  fi
done

# Update exiting translations
for ts_file in ./assets/i18n/*.ts
do
  [ -f "$ts_file" ] || break
  locale=`basename ${ts_file%.*}`
  if [ ./assets/i18n/$locale.po -nt ./assets/i18n/$locale.ts ]
  then
    echo "--- Update $locale from PO-file"
    lconvert ./assets/i18n/$locale.po -o ./assets/i18n/$locale.ts
  else
    # Create *.po-file for accent
    echo "-- Update $locale"
    lconvert ./assets/i18n/$locale.ts -o ./assets/i18n/$locale.po
  fi

  [[ "$locale" == "en" ]] || pylupdate6 --no-obsolete --ts $ts_file .
done
