import subprocess
import sys

is_debug = "debug" in sys.argv

try:
    version = subprocess.check_output(["git", "describe", "--tags"]) \
        .decode("utf8").replace("\n", "")
except subprocess.CalledProcessError:
    print("-- error: can't read git version info")
    sys.exit(1)

text = "VERSION = \"{}\"\nDEBUG_MODE = {}".format(version, is_debug)

with open("src/version_info.py", "w") as f:
    f.write(text)
