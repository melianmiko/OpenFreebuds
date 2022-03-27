import logging
import os

import openfreebuds_backend
from openfreebuds.manager import FreebudsManager
from openfreebuds.device.spp_device import SPPDevice
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import updater
from openfreebuds_applet.settings import SettingsStorage
from mtrayapp import Menu


class QuitingMenu(Menu):
    """
    This menu will appear after clicking "Exit" action
    and will provide force quit option
    """

    # noinspection PyUnresolvedReferences,PyProtectedMember
    def on_build(self):
        self.add_item(t("state_quiting"), enabled=False)
        self.add_item(t("action_kill_app"), action=os._exit, args=[0])


class HeaderMenuPart(Menu):
    """
    This is base menu header. Contains:
    - Update option, if available
    - Device info/unpair submenu
    - Device connect/disconnect button
    """

    def __init__(self, manager: FreebudsManager, settings: SettingsStorage):
        super().__init__()
        self.manager = manager
        self.settings = settings

        self.device_info_menu = DeviceInfoMenu(manager, settings)

    def on_build(self):
        has_update, new_version = updater.get_result()
        device_name = self.settings.device_name
        is_connected = self.manager.state == self.manager.STATE_CONNECTED

        self.add_item(text=t('action_update').format(new_version),
                      action=updater.show_update_message,
                      visible=has_update)

        if self.manager.state != self.manager.STATE_NO_DEV:
            self.add_submenu(text=device_name, menu=self.device_info_menu)

            if is_connected:
                self.add_item(t('action_disconnect'), self.do_disconnect)
            else:
                self.add_item(t('action_connect'), self.do_connect)

        self.add_separator()

    def do_connect(self):
        if self.manager.state == self.manager.STATE_CONNECTED:
            return False

        utils.run_thread_safe(self._do_force_connect, "ForceConnect", False)
        return True

    def do_disconnect(self):
        if self.manager.state != self.manager.STATE_CONNECTED:
            return False

        utils.run_thread_safe(self._do_force_disconnect, "ForceDisconnect", False)
        return True

    def _do_force_connect(self):
        manager = self.manager
        settings = self.settings
        log = logging.getLogger("ForceConnectUI")

        if manager.paused:
            self.application.error_box(t("error_in_work"), "OpenFreebuds")
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
            self.application.error_box(t("error_force_action_fail"), "OpenFreebuds")

        log.debug("Finish force connecting")
        manager.paused = False

    def _do_force_disconnect(self):
        manager = self.manager
        settings = self.settings
        log = logging.getLogger("ForceConnectUI")

        if manager.paused:
            self.application.error_box(t("error_in_work"), "OpenFreebuds")
            return

        manager.paused = True
        log.debug("Trying to force disconnect device...")
        # noinspection PyBroadException
        try:
            if not openfreebuds_backend.bt_disconnect(settings.address):
                raise Exception("fail")
        except Exception:
            log.exception("Can't disconnect device")
            self.application.error_box(t("error_force_action_fail"), "OpenFreebuds")

        log.debug("Finish force disconnecting")
        manager.paused = False


class DeviceInfoMenu(Menu):
    """
    Device info/unpair submenu
    """
    def __init__(self, manager: FreebudsManager, settings: SettingsStorage):
        super().__init__()
        self.manager = manager
        self.settings = settings

    def on_build(self):
        self.add_item(t("submenu_device_info"), self.show_device_info)
        self.add_item(t("action_unpair"), self.do_unpair)

    def show_device_info(self):
        if self.manager.state != self.manager.STATE_CONNECTED:
            self.application.message_box(t("mgr_state_2"), "Device info")
            return

        props = self.manager.device.find_group("info")
        message = "{} ({})\n\n".format(self.settings.device_name, self.settings.address)

        for a in props:
            message += "{}: {}\n".format(a, props[a])

        self.application.message_box(message, "Device info")

    def do_unpair(self):
        self.settings.address = ""
        self.settings.device_name = ""
        self.settings.write()

        self.manager.unset_device(lock=False)
