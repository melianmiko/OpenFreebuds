import os
import subprocess
import sys

NUITKA_ARGS = {
    "nofollow-import-to": [
        # Unused backends
        "evdev",
        "Xlib",
        "tkinter",
        # Unused psutil backends
        "psutil._psosx",
        "psutil._psbsd",
        "psutil._pssunos",
        "psutil._psaix",
        # Huge Pillow plugins
        "PIL.TiffImagePlugin",
        "PIL.GifImagePlugin",
        "PIL.JpegImagePlugin"
    ]
}

NUITKA_ARGS_WINDOWS = {
    "standalone": True,
    "nofollow-import-to": [
        "psutil._pslinux",
        "gi"
    ],
    "include-module": [
        "PIL.IcoImagePlugin",
        "PIL.BmpImagePlugin"
    ]
}

NUITKA_ARGS_LINUX = {
    "follow-imports": True,
    "nofollow-import-to": [
        "psutil._pswindows",
        "PIL.IcoImagePlugin",
        "PIL.BmpImagePlugin",
        "winsdk"
    ]
}


def make():
    # Prepare props
    base_command = ["python", "-m", "nuitka"]
    path = os.getcwd() + "/bin/openfreebuds"
    args = mk_args(NUITKA_ARGS)

    if sys.platform == "win32":
        path = path.replace("/", "\\")
        args += mk_args(NUITKA_ARGS_WINDOWS)
    elif sys.platform == "linux":
        args += mk_args(NUITKA_ARGS_LINUX)

    # Add current dir to $ENV
    os.environ["PYTHONPATH"] = os.getcwd()

    # Go to builddir
    if not os.path.isdir(os.getcwd() + "/builddir"):
        os.mkdir(os.getcwd() + "/builddir")
    os.chdir(os.getcwd() + "/builddir")

    # Build command and run
    command = base_command + args + [path]
    print("-- starting nuitka")
    subprocess.Popen(command).wait()

    # Run UPX
    if sys.platform == "linux":
        print("-- run UPX for bin file")
        subprocess.Popen(["upx", "openfreebuds.bin"]).wait()
    elif sys.platform == "win32":
        print("-- todo: list files for UPX in win32")


def mk_args(args):
    out = []
    for prop in args:
        value = args[prop]
        if isinstance(value, bool) and value:
            out.append("--" + prop)
        elif isinstance(value, list):
            for b in value:
                out.append("--" + prop + "=" + b)
        else:
            out.append("--" + prop + "=" + str(value))
    return out


if __name__ == "__main__":
    make()
