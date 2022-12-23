import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

# Detect theme path
import sv_ttk
SV_PATH = os.path.abspath(os.path.dirname(sv_ttk.__file__))

WINDOWS_PYINSTALLER_ARGS = {
    "name": "openfreebuds",
    "icon": "..\\src\\openfreebuds_assets\\icon.ico",
    "exclude-module": [
    ],
    "add-data": [
        "..\\src\\openfreebuds_assets;openfreebuds_assets",
        f"{SV_PATH};sv_ttk"
    ]
}


def make_win32():
    base_wd = os.getcwd()

    args = mk_args(WINDOWS_PYINSTALLER_ARGS)
    path = base_wd + "\\src\\ofb_launcher.py"

    os.environ["PYTHONPATH"] = base_wd + "/src"
    sys.path.append(base_wd + "/src")

    import version_info

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
    subprocess.Popen([r"C:\Program Files (x86)\NSIS\Bin\makensis", "installer.nsi"]).wait()
    os.rename("openfreebuds.install.exe", "openfreebuds_{}_win64.exe".format(version_info.VERSION))

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
    if not os.path.isdir("src"):
        print("Can't find 'src' folder. Run this script from repo root.")
        raise SystemExit

    if len(sys.argv) < 2 and sys.platform == 'win32':
        print("We think that you want to compile win32 bundle")
        make_win32()
    elif len(sys.argv) < 2:
        print("No command")
