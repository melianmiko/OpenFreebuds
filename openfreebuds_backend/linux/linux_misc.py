import logging
import os
import pathlib
import subprocess

from dbus_next import DBusError

from openfreebuds_backend.linux.dbus.xdg_background import XdgDesktopBackgroundPortal

log = logging.getLogger("OfbLinuxBackend")


def get_app_storage_path():
    if pathlib.Path('/app/is_container').exists():
        return pathlib.Path.home() / ".var/app/pw.mmk.OpenFreebuds/config"
    return pathlib.Path.home() / ".config"


def open_file(path):
    subprocess.Popen(["xdg-open", path])


def is_run_at_boot():
    return os.path.isfile(_get_autostart_file_path())


async def set_run_at_boot(val):
    path = _get_autostart_file_path()
    data = (f"[Desktop Entry]\n"
            f"Name=OpenFreebuds\n"
            f"Categories=GNOME;GTK;Utility;\n"
            f"Exec=openfreebuds_qt\n"
            f"Icon=pw.mmk.OpenFreebuds\n"
            f"Terminal=false\n"
            f"Type=Application\n"
            f"X-KDE-autostart-phase=1\n"
            f"X-GNOME-Autostart-enabled=true\n")

    if val:
        # Install
        with open(path, "w") as f:
            f.write(data)
        log.debug("Created autostart file: " + path)
    else:
        # Remove
        if os.path.isfile(path):
            os.unlink(path)
        log.debug("Removed autostart file: " + path)

    # Sync with DBus (Flatpak)
    try:
        o = await XdgDesktopBackgroundPortal.get()
        res, bg, autostart = await o.request_background(autostart=val)
        assert res and autostart is val
        log.debug(f"Enable autostart through portal success")
    except (AttributeError, AssertionError, DBusError):
        log.debug("Sync with portal failed")


def _get_autostart_file_path():
    if pathlib.Path('/app/is_container').exists():
        return str(get_app_storage_path() / "autostart")

    autostart_dir = pathlib.Path.home() / ".config/autostart"
    if not autostart_dir.exists():
        autostart_dir.mkdir(parents=True)
    return str(autostart_dir / "openfreebuds.desktop")
