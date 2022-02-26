import os
import shutil
import subprocess

VERSION_CODE = "v0.1"

WINDOWS_PYINSTALLER_ARGS = {
    "windowed": True
}


def make_win32():
    if os.path.isdir("builddir/dist"):
        shutil.rmtree("builddir/dist")

    mk_run(["pyinstaller"], WINDOWS_PYINSTALLER_ARGS, os.getcwd() + "\\src\\ofb_launcher.py")

    # Copy assets to bundle
    print("-- copy assets to dest dir")
    shutil.copytree("openfreebuds_assets", "builddir/dist/openfreebuds/openfreebuds_assets")


def mk_run(base_command, arg_set, path):
    base_wd = os.getcwd()
    args = mk_args(arg_set)
    os.environ["PYTHONPATH"] = base_wd + "/src"

    # Go to builddir
    if not os.path.isdir(os.getcwd() + "/builddir"):
        os.mkdir(os.getcwd() + "/builddir")
    os.chdir(os.getcwd() + "/builddir")

    # Build command and run
    command = base_command + args + [path]
    print("-- starting " + base_command[0])
    subprocess.Popen(command).wait()

    os.chdir(base_wd)


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
    make_win32()
