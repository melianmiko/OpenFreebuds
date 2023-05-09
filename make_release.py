import os
import shutil
import subprocess
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import version_info


def main():
	print(f"Make OpenFreebuds {version_info.VERSION}")
	if sys.platform == "win32":
		make_win32()
	else:
		print("OS not supported")


def make_win32():
	if os.path.isdir("dist"):
		shutil.rmtree("dist")

	subprocess.Popen([r"venv\Scripts\pyinstaller.exe", "openfreebuds.spec"]).wait()
	subprocess.Popen([r"C:\Program Files (x86)\NSIS\Bin\makensis.exe", "openfreebuds.nsi"]).wait()

	os.rename(r"dist\openfreebuds.install.exe", f"dist\\openfreebuds_{version_info.VERSION}_win32.exe")


main()
