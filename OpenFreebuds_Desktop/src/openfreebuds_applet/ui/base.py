import logging
import os

import openfreebuds_backend
from openfreebuds.device.huawei_spp_device import HuaweiSPPDevice
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import updater
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

    def __init__(self, applet):
        super().__init__()
        self.manager = applet.manager
        self.settings = applet.settings
        self.applet = applet

    def on_build(self):
        has_update, new_version = updater.get_result()
        device_name = self.settings.device_name
        is_connected = self.manager.state == self.manager.STATE_CONNECTED

        self.add_item(text=t('action_update').format(new_version),
                      action=updater.show_update_message,
                      visible=has_update)

        if self.manager.state != self.manager.STATE_NO_DEV:
            self.add_item(text=device_name, enabled=False)

            if is_connected:
                self.add_item(t('action_disconnect'), self.do_disconnect)
            else:
                self.add_item(t('action_connect'), self.do_connect)

        self.add_separator()

    def do_connect(self):
        if self.manager.state == self.manager.STATE_CONNECTED:
            return False

        self.applet.run_thread(self._do_force_connect, "ForceConnect", False)
        return True

    def do_disconnect(self):
        if self.manager.state != self.manager.STATE_CONNECTED:
            return False

        self.applet.run_thread(self._do_force_disconnect, "ForceDisconnect", False)
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
            spp = HuaweiSPPDevice(settings.address)
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
