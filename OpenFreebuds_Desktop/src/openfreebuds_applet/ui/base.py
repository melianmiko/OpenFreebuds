import logging
import os

import openfreebuds_backend
from openfreebuds import cli_io
from openfreebuds.spp.device import SPPDevice
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import updater
from openfreebuds_applet.wrapper.tray import TrayMenu


class QuitingMenu(TrayMenu):
    """
    This menu will appear after clicking "Exit" action
    and will provide force quit option
    """

    # noinspection PyUnresolvedReferences,PyProtectedMember
    def on_build(self):
        self.add_item(t("state_quiting"), enabled=False)
        self.add_item(t("action_kill_app"), action=os._exit, args=[0])


class HeaderMenuPart(TrayMenu):
    """
    This is base menu header. Contains:
    - Update option, if available
    - Device info/unpair submenu
    - Device connect/disconnect button
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet
        self.device_info_menu = DeviceInfoMenu(applet)

    def on_build(self):
        has_update, new_version = updater.get_result()
        device_name = self.applet.settings.device_name
        is_connected = self.applet.manager.state == self.applet.manager.STATE_CONNECTED

        self.add_item(text=t('action_update').format(new_version),
                      action=updater.show_update_message,
                      visible=has_update)

        if self.applet.manager.state != self.applet.manager.STATE_NO_DEV:
            self.add_submenu(text=device_name, menu=self.device_info_menu)

            if is_connected:
                self.add_item(t('action_disconnect'), self.do_disconnect)
            else:
                self.add_item(t('action_connect'), self.do_connect)

        self.add_separator()

    def do_connect(self):
        manager = self.applet.manager
        if manager.state == manager.STATE_CONNECTED:
            return False

        utils.run_thread_safe(self._do_force_connect, "ForceConnect", False)
        return True

    def do_disconnect(self):
        manager = self.applet.manager
        if manager.state != manager.STATE_CONNECTED:
            return False

        utils.run_thread_safe(self._do_force_disconnect, "ForceDisconnect", False)
        return True

    def _do_force_connect(self):
        manager = self.applet.manager
        settings = self.applet.settings
        log = logging.getLogger("ForceConnectUI")

        if manager.paused:
            openfreebuds_backend.show_message(t("error_in_work"), is_error=True)
            return

        manager.paused = True
        log.debug("Trying to force connect device...")
        # noinspection PyBroadException
        try:
            spp = SPPDevice(settings.address)
            if not spp.request_interaction():
                log.debug("Can't interact via SPP, try to connect anyway...")

            if not openfreebuds_backend.bt_connect(settings.address):
                raise Exception("fail")
        except Exception:
            log.exception("Can't force connect device")
            openfreebuds_backend.show_message(t("error_force_action_fail"), is_error=True)

        log.debug("Finish force connecting")
        manager.paused = False

    def _do_force_disconnect(self):
        manager = self.applet.manager
        settings = self.applet.settings
        log = logging.getLogger("ForceConnectUI")

        if manager.paused:
            openfreebuds_backend.show_message(t("error_in_work"), is_error=True)
            return

        manager.paused = True
        log.debug("Trying to force disconnect device...")
        # noinspection PyBroadException
        try:
            if not openfreebuds_backend.bt_disconnect(settings.address):
                raise Exception("fail")
        except Exception:
            log.exception("Can't disconnect device")
            openfreebuds_backend.show_message(t("error_force_action_fail"), is_error=True)

        log.debug("Finish force disconnecting")
        manager.paused = False


class DeviceInfoMenu(TrayMenu):
    """
    Device info/unpair submenu
    """
    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        self.add_item(t("submenu_device_info"), self.show_device_info)
        self.add_item(t("action_unpair"), self.do_unpair)

        if self.applet.settings.enable_debug_features:
            self.add_item("DEV: Run command", self.do_command)
            self.add_item("DEV: Show logs", self.show_log)

    def show_log(self):
        value = self.applet.log.getvalue()
        path = str(utils.get_app_storage_dir()) + "/last_log.txt"
        with open(path, "w") as f:
            f.write(value)

        openfreebuds_backend.open_file(path)

    def do_command(self):
        openfreebuds_backend.ask_string("openfreebuds>", self.on_command)

    def on_command(self, result):
        if result is None or result == "":
            return

        command = result.split(" ")
        result = cli_io.dev_command(self.applet.manager, command)
        openfreebuds_backend.show_message(result)

    def show_device_info(self):
        if self.applet.manager.state != self.applet.manager.STATE_CONNECTED:
            openfreebuds_backend.show_message(t("mgr_state_2"))
            return

        dev = self.applet.manager.device
        settings = self.applet.settings
        props = dev.find_group("info")

        message = "{} ({})\n\n".format(settings.device_name, settings.address)

        for a in props:
            message += "{}: {}\n".format(a, props[a])

        openfreebuds_backend.show_message(message)

    def do_unpair(self):
        self.applet.settings.address = ""
        self.applet.settings.device_name = ""
        self.applet.settings.write()

        self.applet.manager.unset_device(lock=False)
