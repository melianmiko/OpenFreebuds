import os
import subprocess
import sys

NOFOLLOW_GLOBAL = [
    # Unused backends
    "evdev",
    "Xlib",
    # Huge Pillow plugins
    "PIL.TiffImagePlugin",
    "PIL.GifImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.BmpImagePlugin"
]

NOFOLLOW_WINDOWS = [
    "psutil._pslinux",
    "psutil._psosx",
    "gi"
]

NOFOLLOW_LINUX = [
    "psutil._pswindows",
    "psutil._psosx",
    "winsdk"
]


def make():
    # Prepare props
    base_command = ["python", "-m", "nuitka"]
    path = os.getcwd() + "/bin/openfreebuds"
    mode = "--follow-imports"
    args = mk_nofollow(NOFOLLOW_GLOBAL)

    if sys.platform == "win32":
        path = path.replace("/", "\\")
        mode = "--standalone"
        args += mk_nofollow(NOFOLLOW_WINDOWS)
    elif sys.platform == "linux":
        args += mk_nofollow(NOFOLLOW_LINUX)

    # Add current dir to $ENV
    os.environ["PYTHONPATH"] = os.getcwd()

    # Go to builddir
    if not os.path.isdir(os.getcwd() + "/builddir"):
        os.mkdir(os.getcwd() + "/builddir")
    os.chdir(os.getcwd() + "/builddir")

    # Build command and run
    command = base_command + [mode] + args + [path]
    print("Running", command)
    subprocess.Popen(command).wait()


def mk_nofollow(excludes):
    out = []
    for a in excludes:
        out.append("--nofollow-import-to=" + a)
    return out


if __name__ == "__main__":
    make()
