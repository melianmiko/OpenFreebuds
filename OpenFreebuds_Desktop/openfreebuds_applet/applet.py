import logging
import threading
import time
import webbrowser

import pystray
from PIL import Image, ImageDraw

import openfreebuds.manager
import openfreebuds_applet.settings
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui.base import get_header_menu_part, get_app_menu_part
import openfreebuds_applet.ui.device_scan
import openfreebuds_applet.ui.device_offline
import openfreebuds_applet.ui.device_menu
import openfreebuds_applet.platform_tools as pt

log = logging.getLogger("Applet")


def create_image():
    width = 24
    height = 24
    color1 = "#FFFFFF"
    color2 = "#0099FF"

    # Generate an image and draw a pattern
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)

    return image


class FreebudsApplet:
    def __init__(self):
        self.manager = openfreebuds.manager.create()
        self.tray = pystray.Icon(name="OpenFreebuds",
                                 title="OpenFreebuds",
                                 icon=create_image(),
                                 menu=pystray.Menu())

        self.started = False
        self.on_exit = threading.Event()

        self.selected_device_address = ""
        self.device_selected = threading.Event()

        self.settings = openfreebuds_applet.settings.SettingsStorage()

    def start(self):
        if not self.tray.HAS_MENU:
            result = pt.show_question(t("no_menu_error_info"),
                                      t("no_menu_error_title"))
            if result == pt.RESULT_YES:
                webbrowser.open("https://melianmiko.ru/openfreebuds")
            return

        threading.Thread(target=self._mainloop).start()
        self.tray.run()

    def drop_device(self):
        self.settings.address = ""
        self.settings.device_name = ""
        self.manager.unset_device()

    def exit(self):
        log.info("Exiting this app...")
        self.started = False
        self.manager.unset_device()
        self.tray.stop()

        self.on_exit.wait()

    def set_menu_items(self, items, expand=False):
        if expand:
            items = get_header_menu_part(self) + items

        items += get_app_menu_part(self)
        menu = pystray.Menu(*items)
        self.tray.menu = menu

    # Main UI render loop
    def _mainloop(self):
        self.started = True
        self.on_exit.clear()

        if self.settings.address != "":
            log.info("Using saved address: " + self.settings.address)
            self.manager.set_device(self.settings.address)
        else:
            pt.show_message(t("first_run_message"),
                            t("first_run_title"))

        while self.started:
            log.debug("state=" + str(self.manager.state))
            if self.manager.state == self.manager.STATE_NO_DEV:
                openfreebuds_applet.ui.device_scan.loop(self)
            elif self.manager.state == self.manager.STATE_CONNECTED:
                openfreebuds_applet.ui.device_menu.loop(self)
            else:
                openfreebuds_applet.ui.device_offline.loop(self)
            time.sleep(1)

        self.manager.close()
        self.on_exit.set()
