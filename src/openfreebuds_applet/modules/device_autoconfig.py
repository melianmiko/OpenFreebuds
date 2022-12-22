import logging
import threading

import openfreebuds_backend
from openfreebuds import device
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.settings import SettingsStorage

autoconf_lock = threading.Lock()
log = logging.getLogger("AutoConfig")


def process(manager: FreebudsManager, settings: SettingsStorage):
    if not settings.device_autoconfig or manager.state > 1:
        return

    if not autoconf_lock.acquire(blocking=False):
        # Already locked
        return

    log.info("Attempt to change device automatically")
    paired_devices = openfreebuds_backend.bt_list_devices()

    for bt_dev in paired_devices:
        if not bt_dev["connected"]:
            continue

        name = bt_dev["name"]
        address = bt_dev["address"]
        if device.is_supported(name):
            log.info(f"Use {name} {address}")
            manager.set_device(name, address)

            if settings.address != address:
                settings.device_name = name
                settings.address = address
                settings.write()

            break

    autoconf_lock.release()
