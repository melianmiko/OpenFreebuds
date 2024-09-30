#!/usr/bin/env python3

"""
Unified Linux build/install script for OpenFreebuds
Should work in (mostly) all distributions
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from sys import version_info

PROJECT_ROOT = Path(__file__).parent
if PROJECT_ROOT.name == "scripts":
    PROJECT_ROOT = PROJECT_ROOT.parent

# Constants
DEFAULT_DESTINATION = "/usr/local"
PYTHON_XX = f"python{version_info.major}.{version_info.minor}"
PYTHON_LIB_PATH_OPTIONS = [
    f"lib/{PYTHON_XX}/dist-packages",
    f"lib/python3/dist-packages",
    f"lib/python/dist-packages",
    f"lib/{PYTHON_XX}/site-packages",
    f"lib/python3/site-packages",
    f"lib/python/site-packages",
]
QT_L_RELEASE_PATH_OPTIONS = [
    "/usr/lib/qt6/bin/lrelease",
    "/usr/bin/lrelease",
    "lrelease",
]
ALLOWED_TASKS = [
    "build",
    "install",
    "build_install",
    "launch",
    "build_launch"
]

# Base params
if len(sys.argv) < 2 or sys.argv[1] not in ALLOWED_TASKS:
    print(f"Usage: ./make.py <{'|'.join(ALLOWED_TASKS)}> [DEST_DIR] [PYTHON_LIBS_DIR]")
    raise SystemExit(1)
TASK = sys.argv[1]
DEST_DIR = Path(DEFAULT_DESTINATION if len(sys.argv) < 3 else sys.argv[2])
PYTHON_LIBS_DIR = None if len(sys.argv) < 4 else Path(sys.argv[3])

# Determinate task
DO_INSTALL = "install" in TASK
DO_LAUNCH = "launch" in TASK
DO_BUILD = "build" in TASK

# Ensure environment
if sys.platform == "win32" and TASK != "build":
    print("-- Can't install under Windows, use pyinstaller")
    raise SystemExit(1)
if os.environ.get("VIRTUAL_ENV", None) is not None:
    print("-- Launch this script outside of virtualenv")
    raise SystemExit(1)

# Find python dest dir
if PYTHON_LIBS_DIR is None:
    for option in PYTHON_LIB_PATH_OPTIONS:
        if (DEST_DIR / option).exists():
            PYTHON_LIBS_DIR = DEST_DIR / option
            PYTHON_LIBS_DIR.mkdir(exist_ok=True, parents=True)
            break

if PYTHON_LIBS_DIR is None:
    print("-- Error: Can't find python packages location, provide them manually")
    raise SystemExit(1)

print(f"Going to {TASK} OpenFreebuds")
if DO_INSTALL:
    print(f"root={DEST_DIR}, python_libs={PYTHON_LIBS_DIR}")

# Source compilation tasks
if DO_BUILD:
    # Compile Qt Designer layouts
    print("Compile Qt Designer files")
    DESIGNER_DIR = PROJECT_ROOT / "openfreebuds_qt" / "designer"
    result = subprocess.run(["env", "poetry", "run", "pyuic6", DESIGNER_DIR])
    if result.returncode != 0:
        print("Failed, old pyuic? Will try single file mode...")
        for ui_file in DESIGNER_DIR.iterdir():
            if not ui_file.name.endswith(".ui"):
                continue
            print(f"Compile {ui_file}")
            result = subprocess.run(["poetry", "run", "pyuic6",
                                     "-o", str(ui_file).replace(".ui", ".py"),
                                     ui_file])
            if result.returncode != 0:
                print("-- PyUiC failed")
                raise SystemExit(1)

    # Compile Qt translations
    L_RELEASE_EXEC = None
    for option in QT_L_RELEASE_PATH_OPTIONS:
        if Path(option).exists():
            L_RELEASE_EXEC = option
            break

    if L_RELEASE_EXEC is not None:
        print("Compile Qt translations")
        files_to_compile = []
        for translation in (PROJECT_ROOT / "openfreebuds_qt/assets/i18n").iterdir():
            if not translation.name.endswith(".ts"):
                continue
            files_to_compile.append(str(translation))
        result = subprocess.run([L_RELEASE_EXEC, "-silent", *files_to_compile])
        if result.returncode != 0:
            print("-- lrelease failed")
            raise SystemExit(1)
    else:
        print("Warn: Can't find Qt lrelease executable, skip compiling translations")

    # Compile Python bundle
    print("Compile Python wheel")
    POETRY_DIST = PROJECT_ROOT / "dist"
    shutil.rmtree(POETRY_DIST, ignore_errors=True)
    result = subprocess.run(["poetry", "build", "-q"])
    if result.returncode != 0:
        print("-- Poetry build failed")
        raise SystemExit(1)

# Launch task
if DO_LAUNCH:
    print('----------------------------------------------------------------')
    print("Launching OpenFreebuds")
    subprocess.run(["poetry", "run", "python", "-m", "openfreebuds_qt", "-vcs"])
    raise SystemExit(0)

# Wheel install tasks
if DO_INSTALL:
    DISTRIBUTION_PATH = PROJECT_ROOT if not (PROJECT_ROOT / "dist").exists() else PROJECT_ROOT / "dist"
    WHEEL_FILE = list(DISTRIBUTION_PATH.glob("*.whl"))
    if len(WHEEL_FILE) == 0:
        print("-- Error: Can't find wheel file to install")
        raise SystemExit(1)
    WHEEL_FILE = WHEEL_FILE[0]

    # Install python package
    print("Install openfreebuds python package")
    result = subprocess.run(["pip", "install", "-q",
                             "--upgrade",
                             "--no-dependencies",
                             f"--target={PYTHON_LIBS_DIR}",
                             WHEEL_FILE])
    if result.returncode != 0:
        print("-- pip package install failure")
        raise SystemExit(1)

    # Install binaries
    BIN_DIR = PYTHON_LIBS_DIR / "bin"
    TARGET_BIN_DIR = DEST_DIR / "bin"
    TARGET_BIN_DIR.mkdir(exist_ok=True, parents=True)

    if BIN_DIR != TARGET_BIN_DIR:
        for filename in ["openfreebuds_qt", "openfreebuds_cmd"]:
            print(f"Install {TARGET_BIN_DIR / filename}")
            shutil.copy(BIN_DIR / filename, TARGET_BIN_DIR)
            os.unlink(BIN_DIR / filename)
    print(f"Install {TARGET_BIN_DIR}/openfreebuds (symlink)")
    (TARGET_BIN_DIR / "openfreebuds").unlink(missing_ok=True)
    os.symlink("./openfreebuds_qt", TARGET_BIN_DIR / "openfreebuds")

    # Copy desktop integration files to system environment
    ASSETS_DIR = PYTHON_LIBS_DIR / "openfreebuds_qt" / "assets"


    def install_asset(asset, dest):
        full_dest = DEST_DIR / dest
        full_dest.mkdir(exist_ok=True, parents=True)
        print(f"Install {full_dest / asset}")
        shutil.copy(ASSETS_DIR / asset, full_dest / asset)


    install_asset("pw.mmk.OpenFreebuds.desktop", "share/applications")
    install_asset("pw.mmk.OpenFreebuds.metainfo.xml", "share/metainfo")
    install_asset("pw.mmk.OpenFreebuds.png", "share/icons/hicolor/256x256/apps")

    print("Done")
