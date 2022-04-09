import logging
import os
import signal
import threading
import traceback
from io import StringIO

import mtrayapp

import openfreebuds.manager
from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED, EVENT_DEVICE_PROP_CHANGED, \
    EVENT_MANAGER_STATE_CHANGED
from openfreebuds.device.base import BaseDevice
from openfreebuds_applet import settings, utils, log_format
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import hotkeys, http_server, updater
from openfreebuds_applet.ui import icons, tk_tools
from openfreebuds_applet.ui.base import QuitingMenu
from openfreebuds_applet.ui.menu_device import DeviceMenu
from openfreebuds_applet.ui.menu_no_device import DeviceOfflineMenu, DeviceScanMenu

log = logging.getLogger("Applet")


class FreebudsApplet:
    def __init__(self):
        super().__init__()
        self.started = False
        self.allow_ui_update = False
        self.current_menu_hash = ""
        self.current_icon_hash = ""

        self.settings = settings.SettingsStorage()
        self.log = StringIO()

        self.manager = openfreebuds.manager.create()
        self.manager.config.SAFE_RUN_WRAPPER = self.run_thread
        self.manager.config.USE_SOCKET_SLEEP = self.settings.enable_sleep

        self.menu_offline = DeviceOfflineMenu(self)
        self.menu_scan = DeviceScanMenu(self)
        self.menu_device = DeviceMenu(self)

        self.tray_application = mtrayapp.TrayApplication(name="OpenFreebuds",
                                                         title="OpenFreebuds",
                                                         icon=icons.generate_icon(1),
                                                         menu=mtrayapp.Menu())

    def start(self):
        self._safe_run_wrapper(self._start, "MainThread", True)

    def _start(self):
        icons.set_theme(self.settings.icon_theme)
        tk_tools.set_theme(self.settings.theme)

        hotkeys.start(self)
        http_server.start(self)
        updater.start(self)

        if self.settings.enable_debug_features:
            self._enable_debug_logging()

        self._setup_ctrl_c()
        self.run_thread(self._ui_update_loop, "Applet", True)
        self.tray_application.run()

    def _setup_ctrl_c(self):
        # noinspection PyUnresolvedReferences,PyProtectedMember
        def _handle_ctrl_c(_, __):
            if not self.started:
                os._exit(1)
            log.debug("Leaving, press Ctrl-C again to force exit")
            self.exit()

        try:
            signal.signal(signal.SIGINT, _handle_ctrl_c)
        except ValueError:
            pass

    def run_thread(self, target, display_name, critical):
        log.debug("Running new thread, display_name={}".format(display_name))
        thread = threading.Thread(target=self._safe_run_wrapper, args=(target, display_name, critical))
        thread.start()
        return thread

    def exit(self):
        log.info("Exiting this app...")
        self.tray_application.menu = QuitingMenu()

        self.allow_ui_update = False
        self.started = False
        event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)

    def update_icon(self):
        if not self.allow_ui_update:
            return

        mgr_state = self.manager.state
        battery = 0
        noise_mode = 0

        if mgr_state == self.manager.STATE_CONNECTED:
            dev = self.manager.device  # type: BaseDevice

            battery_left = dev.find_property("battery", "left", 0)
            battery_right = dev.find_property("battery", "right", 0)
            if battery_left == 0:
                battery_left = 100
            if battery_right == 0:
                battery_right = 100
            noise_mode = dev.find_property("anc", "mode", 0)
            battery = min(battery_right, battery_left)

        new_hash = icons.get_hash(mgr_state, battery, noise_mode)
        if self.current_icon_hash == new_hash:
            return

        self.tray_application.icon = icons.generate_icon(mgr_state, battery, noise_mode)
        self.current_icon_hash = new_hash

    def apply_menu(self, menu):
        if not self.allow_ui_update:
            return

        items_hash = utils.items_hash_string(menu.items)
        if self.current_menu_hash != items_hash:
            self.current_menu_hash = items_hash
            self.tray_application.menu = menu

            log.debug("Menu updated, hash=" + items_hash)

    def _enable_debug_logging(self):
        print("Start debug logging mode")
        logging.basicConfig(level=logging.DEBUG, format=log_format, force=True)

        handler = logging.StreamHandler(self.log)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(log_format))
        for a in ["SPPDevice", "FreebudsManager", "BaseDevice"]:
            logging.getLogger(a).addHandler(handler)

    def _safe_run_wrapper(self, f, display_name, critical, args=None):
        message = "An unhandled exception was caught in thread {}.\n\n{}"
        if critical:
            message += "\nThis exception is critical. App will be closed."
        if args is None:
            args = []

        # noinspection PyBroadException
        try:
            f(*args)
        except Exception:
            exc_text = traceback.format_exc()
            logging.getLogger("RunSafe").exception("Action {} failed.".format(display_name))
            self.tray_application.message_box(message.format(display_name, exc_text),
                                              "OpenFreebuds Error")
            if critical:
                # noinspection PyProtectedMember,PyUnresolvedReferences
                os._exit(99)

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
            self.manager.set_device(self.settings.device_name, self.settings.address)
        else:
            tk_tools.message(t("first_run_message"), "Welcome")

        while self.started:
            self.update_icon()
            if self.manager.state == self.manager.STATE_NO_DEV:
                self.apply_menu(self.menu_scan)
            elif self.manager.state == self.manager.STATE_CONNECTED:
                self.apply_menu(self.menu_device)
            else:
                self.apply_menu(self.menu_offline)
            event_queue.wait()

        self.manager.close()
        self.tray_application.stop()
        log.info("Tray stopped, exiting...")

        # noinspection PyProtectedMember,PyUnresolvedReferences
        os._exit(0)
