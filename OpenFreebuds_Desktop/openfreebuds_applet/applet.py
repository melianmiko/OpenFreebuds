import logging
import os

import openfreebuds.manager
import openfreebuds_backend
from openfreebuds import event_bus
from openfreebuds.events import EVENT_UI_UPDATE_REQUIRED, EVENT_DEVICE_PROP_CHANGED, EVENT_MANAGER_STATE_CHANGED
from openfreebuds.spp.device import SPPDevice
from openfreebuds_applet import tools, settings, icons, tool_server, tool_hotkeys
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import base_ui, device_menu, device_scan_menu, device_offline_menu

log = logging.getLogger("Applet")


class FreebudsApplet:
    def __init__(self):
        self.started = False
        self.allow_ui_update = False
        self.current_menu_hash = ""
        self.current_icon_hash = ""

        self.settings = settings.SettingsStorage()
        icons.set_theme(self.settings.theme)

        self.manager = openfreebuds.manager.create()
        self.manager.safe_run_wrapper = tools.run_thread_safe

        self._tray = openfreebuds_backend.TrayIcon(name="OpenFreebuds",
                                                   title="OpenFreebuds",
                                                   icon=icons.get_icon_offline(),
                                                   menu=openfreebuds_backend.Menu())

    def drop_device(self):
        self.settings.address = ""
        self.settings.device_name = ""

        self.settings.write()

        self.manager.unset_device(lock=False)

    # noinspection PyBroadException
    def force_connect(self):
        if self.manager.paused:
            openfreebuds_backend.show_message(t("error_in_work"), "Openfreebuds", is_error=True)
            return False

        tools.run_thread_safe(self._do_force_connect, "ForceConnect", False)
        return True

    def _do_force_connect(self):
        self.manager.paused = True

        log.debug("Trying to force connect device...")
        spp = SPPDevice(self.settings.address)
        if not spp.request_interaction():
            log.debug("Can't interact via SPP, try to connect anyway...")

        if not openfreebuds_backend.bt_connect(self.settings.address):
            openfreebuds_backend.show_message(t("error_force_action_fail"), is_error=True)

        log.debug("Finish force connecting")
        self.manager.paused = False

    # noinspection PyBroadException
    def force_disconnect(self):
        if self.manager.paused:
            openfreebuds_backend.show_message(t("error_in_work"), "Openfreebuds", is_error=True)
            return False

        tools.run_thread_safe(self._do_force_disconnect, "ForceDisconnect", False)
        return True

    def _do_force_disconnect(self):
        self.manager.paused = True
        log.debug("Trying to force disconnect device...")

        if not openfreebuds_backend.bt_disconnect(self.settings.address):
            openfreebuds_backend.show_message(t("error_force_action_fail"), is_error=True)

        log.debug("Finish force disconnecting")
        self.manager.paused = False

    def start(self):
        tool_hotkeys.start(self)
        tool_server.start(self)

        tools.run_thread_safe(self._ui_update_loop, "Applet", True)

        self._tray.run()

    def exit(self):
        log.info("Exiting this app...")
        items = base_ui.get_quiting_menu()
        menu = openfreebuds_backend.Menu(*items)
        self._tray.menu = menu

        self.allow_ui_update = False
        self.started = False
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def set_theme(self, name):
        icons.set_theme(name)

        self.settings.theme = name
        self.settings.write()

        # Wipe hash for icon reload
        self.current_icon_hash = ""

        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

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
            items = base_ui.get_header_menu_part(self) + items

        items += base_ui.get_app_menu_part(self)
        items_hash = tools.items_hash_string(items)

        if self.current_menu_hash != items_hash:
            menu = openfreebuds_backend.Menu(*items)

            self.current_menu_hash = items_hash
            self._tray.menu = menu

            log.debug("Menu updated, hash=" + items_hash)

    def _ui_update_loop(self):
        self.started = True
        self.allow_ui_update = True

        event_queue = event_bus.register([
            EVENT_UI_UPDATE_REQUIRED,
            EVENT_DEVICE_PROP_CHANGED,
            EVENT_MANAGER_STATE_CHANGED
        ])

        if self.settings.address != "":
            log.info("Using saved address: " + self.settings.address)
            self.manager.set_device(self.settings.address)
        else:
            openfreebuds_backend.show_message(t("first_run_message"),
                                              t("first_run_title"))

        while self.started:
            if self.manager.state == self.manager.STATE_NO_DEV:
                device_scan_menu.process(self)
            elif self.manager.state == self.manager.STATE_CONNECTED:
                device_menu.process(self)
            else:
                device_offline_menu.process(self)
            event_queue.wait()

        self.manager.close()
        self._tray.stop()
        log.info("Tray stopped, exiting...")

        # noinspection PyProtectedMember,PyUnresolvedReferences
        os._exit(0)
