import sys
import polib

po = polib.pofile(sys.argv[1])
for entry in po:
    if entry.msgstr == "":
        entry.msgstr = entry.msgid

po.save(sys.argv[1])
