import os
import shutil
import subprocess

WINDOWS_PYINSTALLER_ARGS = {
    "name": "openfreebuds",
    "icon": "..\\src\\openfreebuds_assets\\icon.ico",
    "windowed": True,
    "add-data": [
        "..\\src\\openfreebuds_assets;openfreebuds_assets"
    ]
}


def make_win32():
    base_wd = os.getcwd()
    args = mk_args(WINDOWS_PYINSTALLER_ARGS)
    path = base_wd + "\\src\\ofb_launcher.py"

    os.environ["PYTHONPATH"] = base_wd + "/src"

    # Go to builddir
    if not os.path.isdir(os.getcwd() + "/builddir"):
        os.mkdir(os.getcwd() + "/builddir")
    if os.path.isdir("builddir/dist"):
        shutil.rmtree("builddir/dist")

    # Build command and run
    command = ["pyinstaller"] + args + [path]
    print("-- starting", command)
    os.chdir(base_wd + "/builddir")
    subprocess.Popen(command).wait()

    # Run nsis
    shutil.copy(base_wd + "/tools/installer.nsi", base_wd + "/builddir/dist/installer.nsi")
    print("-- makensis...")
    os.chdir(base_wd + "/builddir/dist")
    subprocess.Popen(["makensis", "installer.nsi"]).wait()

    os.chdir(base_wd)


def mk_args(args):
    out = []
    for prop in args:
        value = args[prop]
        if isinstance(value, bool) and value:
            out.append("--" + prop)
        elif isinstance(value, list):
            for b in value:
                out.append("--" + prop)
                out.append(b)
        else:
            out.append("--" + prop + "=" + str(value))
    return out


if __name__ == "__main__":
    make_win32()
