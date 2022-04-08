import logging
import os
import pathlib
import subprocess

log = logging.getLogger("LinuxBackend")


def get_app_storage_path():
    return pathlib.Path.home() / ".config"


def open_in_file_manager(path):
    subprocess.Popen(["xdg-open", path])


def open_file(path):
    subprocess.Popen(["xdg-open", path])


def is_run_at_boot():
    return os.path.isfile(_get_autostart_file_path())


def set_run_at_boot(val):
    path = _get_autostart_file_path()
    data = _mk_autostart_file_content()

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


def _get_autostart_file_path():
    autostart_dir = pathlib.Path.home() / ".config/autostart"
    if not autostart_dir.exists():
        autostart_dir.mkdir()
    return str(autostart_dir / "openfreebuds.desktop")


def _mk_autostart_file_content():
    return (f"[Desktop Entry]\n"
            f"Name=Openfreebuds\n"
            f"Categories=GNOME;GTK;Utility;\n"
            f"Exec=/usr/bin/openfreebuds\n"
            f"Icon=/opt/openfreebuds/openfreebuds_assets/icon.png\n"
            f"Terminal=false\n"
            f"Type=Application\n"
            f"X-GNOME-Autostart-enabled=true\n")
