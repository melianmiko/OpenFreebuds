import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

TTK_THEME_URL = "https://github.com/rdbende/Sun-Valley-ttk-theme/archive/refs/heads/master.zip"

WINDOWS_PYINSTALLER_ARGS = {
    "name": "openfreebuds",
    "icon": "..\\src\\openfreebuds_assets\\icon.ico",
    "windowed": True,
    "exclude-module": [
        "PIL.ImageTk"
    ],
    "add-data": [
        "..\\src\\openfreebuds_assets;openfreebuds_assets"
    ]
}


def make_win32():
    base_wd = os.getcwd()

    if not os.path.isdir(base_wd + "/src/openfreebuds_assets/ttk_theme"):
        download_ttk_theme()

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
    subprocess.Popen([r"C:\Program Files (x86)\NSIS\Bin\makensis", "installer.nsi"]).wait()

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


def download_ttk_theme():
    base_wd = os.getcwd()
    os.chdir(base_wd + "/src/openfreebuds_assets")
    if os.path.isdir("ttk_theme"):
        print("Deleting exiting theme...")
        shutil.rmtree("ttk_theme")

    print("Downloading theme...")
    with urllib.request.urlopen(TTK_THEME_URL) as dl_file:
        with open("ttk_theme.zip", 'wb') as out_file:
            out_file.write(dl_file.read())

    print("Extracting")
    with zipfile.ZipFile("ttk_theme.zip", "r") as theme_zip:
        dirname = theme_zip.namelist()[0]
        theme_zip.extractall()

    os.rename(dirname[:-1], "ttk_theme")
    os.unlink("ttk_theme.zip")
    os.unlink("ttk_theme/DOCUMENTATION.pdf")
    os.unlink("ttk_theme/Screenshot.png")
    print("ready")
    os.chdir(base_wd)


if __name__ == "__main__":
    if not os.path.isdir("src"):
        print("Can't find 'src' folder. Run this script from repo root.")
        raise SystemExit

    if len(sys.argv) < 2 and sys.platform == 'win32':
        print("We think that you want to compile win32 bundle")
        make_win32()
    elif len(sys.argv) < 2:
        print("No command")
    elif sys.argv[1] == "ttk_theme":
        download_ttk_theme()
