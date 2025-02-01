from pathlib import Path

VERSION_CODE = "noversion"
DIST = Path(__file__).parent / "dist"

with open("openfreebuds.nsi", "r") as f:
	for line in f.read().split("\n"):
		if line.startswith("!define APP_VERSION"):
			VERSION_CODE = line.split(" ")[2][1:-1]
			break

if (DIST / "openfreebuds_portable.exe").is_file():
	(DIST / "openfreebuds_portable.exe").rename(
		DIST / f"openfreebuds_{VERSION_CODE}_win32_portable.exe"
	)

if (DIST / "openfreebuds.install.exe").is_file():
	(DIST / "openfreebuds.install.exe").rename(
		DIST / f"openfreebuds_{VERSION_CODE}_win32.exe"
	)
