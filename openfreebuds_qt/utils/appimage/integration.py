"""
Desktop integration for the AppImage build.

The AppImage runtime exports APPIMAGE with the path of the running file.
"""
import os
import shutil
import subprocess
from pathlib import Path

from openfreebuds_backend.linux.linux_misc import quote_exec
from openfreebuds_qt.constants import ASSETS_PATH

DESKTOP_ID = "pw.mmk.OpenFreebuds"


def appimage_path() -> Path | None:
    value = os.environ.get("APPIMAGE")
    return Path(value) if value else None


def install_path() -> Path:
    return Path.home() / "Applications" / "OpenFreebuds.AppImage"


def _data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def desktop_entry_path() -> Path:
    return _data_home() / "applications" / f"{DESKTOP_ID}.desktop"


def icon_path() -> Path:
    return _data_home() / "icons" / "hicolor" / "256x256" / "apps" / f"{DESKTOP_ID}.png"


def is_installed() -> bool:
    """Running from ~/Applications with a menu entry"""
    current = appimage_path()
    return (current is not None
            and current.resolve() == install_path().resolve()
            and desktop_entry_path().is_file())


def desktop_entry(exec_path: Path) -> str:
    return (f"[Desktop Entry]\n"
            f"Type=Application\n"
            f"Name=OpenFreebuds\n"
            f"GenericName=Headphones manager\n"
            f"Comment=Open-source client app for HUAWEI FreeBuds earphones\n"
            f"Icon={DESKTOP_ID}\n"
            f"Exec={quote_exec(str(exec_path))}\n"
            f"TryExec={exec_path}\n"
            f"Terminal=false\n"
            f"Categories=Settings;HardwareSettings;\n"
            f"Keywords=huawei;headphones;headset;earphones;\n")


def install() -> Path:
    """
    Copy the running AppImage to ~/Applications and add it to the application menu.
    Returns the installed path.
    """
    source = appimage_path()
    if source is None:
        raise RuntimeError("Not running from an AppImage")

    target = install_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        part = target.with_name(target.name + ".part")
        shutil.copyfile(source, part)
        part.chmod(0o755)
        os.replace(part, target)

    icon_path().parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ASSETS_PATH / f"{DESKTOP_ID}.png", icon_path())
    desktop_entry_path().parent.mkdir(parents=True, exist_ok=True)
    desktop_entry_path().write_text(desktop_entry(target))
    _refresh_menu()
    return target


def uninstall():
    """Remove the menu entry, the icon and the installed AppImage"""
    for path in (desktop_entry_path(), icon_path(), install_path()):
        path.unlink(missing_ok=True)
    _refresh_menu()


def _refresh_menu():
    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(desktop_entry_path().parent)],
                       check=False, capture_output=True)


def relaunch(path: Path):
    """Start the AppImage at path once this process released its single-instance lock"""
    subprocess.Popen(["sh", "-c", 'sleep 2; exec "$0"', str(path)], start_new_session=True)
