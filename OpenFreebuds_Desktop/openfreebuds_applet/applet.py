import logging
import threading
import webbrowser

import pystray

import openfreebuds.manager
import openfreebuds_applet.platform_tools as platform_tools
import openfreebuds_applet.settings
import openfreebuds_applet.ui.base
import openfreebuds_applet.ui.device_menu
import openfreebuds_applet.ui.device_offline
import openfreebuds_applet.ui.device_scan
from openfreebuds import event_bus
from openfreebuds_applet import icons
from openfreebuds_applet.l18n import t

log = logging.getLogger("Applet")


def _show_no_tray_warn():
    result = platform_tools.show_question(t("no_menu_error_info"),
                                          t("no_menu_error_title"))

    if result == platform_tools.RESULT_YES:
        webbrowser.open("https://melianmiko.ru/openfreebuds")


class FreebudsApplet:
    def __init__(self):
        self.started = False
        self.allow_ui_update = False
        self.current_menu_hash = ""
        self.current_icon_hash = ""

        self.manager = openfreebuds.manager.create()
        self._tray = pystray.Icon(name="OpenFreebuds",
                                  title="OpenFreebuds",
                                  icon=icons.get_icon_offline(),
                                  menu=pystray.Menu())

        self.settings = openfreebuds_applet.settings.SettingsStorage()

    def drop_device(self):
        self.settings.address = ""
        self.settings.device_name = ""

        self.settings.write()

        self.manager.unset_device(lock=False)

    def exit(self):
        log.info("Exiting this app...")
        items = openfreebuds_applet.ui.base.get_quiting_menu()
        menu = pystray.Menu(*items)
        self._tray.menu = menu

        self.allow_ui_update = False
        self.started = False
        self.manager.unset_device(lock=False)

    def set_tray_icon(self, icon, hashsum):
        if not self.allow_ui_update:
            return

        if self.current_icon_hash == hashsum:
            return

        log.debug("icon changed, new hash=" + hashsum)
        self.current_icon_hash = hashsum
        self._tray.icon = icon

    def set_menu_items(self, items, expand=False):
        if not self.allow_ui_update:
            return

        if expand:
            items = openfreebuds_applet.ui.base.get_header_menu_part(self) + items

        items += openfreebuds_applet.ui.base.get_app_menu_part(self)
        items_hash = openfreebuds_applet.ui.base.items_hash_string(items)

        if self.current_menu_hash != items_hash:
            menu = pystray.Menu(*items)

            self.current_menu_hash = items_hash
            self._tray.menu = menu

            log.debug("Menu updated, hash=" + items_hash)

    def start(self):
        if not self._tray.HAS_MENU:
            _show_no_tray_warn()
            return

        threading.Thread(target=self._mainloop).start()
        self._tray.run()

    def _mainloop(self):
        self.started = True
        self.allow_ui_update = True

        if self.settings.address != "":
            log.info("Using saved address: " + self.settings.address)
            self.manager.set_device(self.settings.address)
        else:
            platform_tools.show_message(t("first_run_message"),
                                        t("first_run_title"))

        while self.started:
            if self.manager.state == self.manager.STATE_NO_DEV:
                openfreebuds_applet.ui.device_scan.process(self)
            elif self.manager.state == self.manager.STATE_CONNECTED:
                openfreebuds_applet.ui.device_menu.process(self)
            else:
                openfreebuds_applet.ui.device_offline.process(self)
            event_bus.wait_any()

        self.manager.close()
        self._tray.stop()
