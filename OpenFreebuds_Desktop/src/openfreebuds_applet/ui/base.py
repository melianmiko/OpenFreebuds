import logging

import openfreebuds_backend
from openfreebuds.spp.device import SPPDevice
from openfreebuds_applet import tools, tool_update
from openfreebuds_applet.l18n import t
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
        has_update, new_version = tool_update.get_result()
        device_name = self.applet.settings.device_name
        is_connected = self.applet.manager.state == self.applet.manager.STATE_CONNECTED

        self.add_item(text=t('action_update').format(new_version),
                      action=tool_update.show_update_message,
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

        tools.run_thread_safe(self._do_force_connect, "ForceConnect", False)
        return True

    def do_disconnect(self):
        manager = self.applet.manager
        if manager.state != manager.STATE_CONNECTED:
            return False

        tools.run_thread_safe(self._do_force_disconnect, "ForceDisconnect", False)
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

    def show_device_info(self):
        if self.applet.manager.state != self.applet.manager.STATE_CONNECTED:
            openfreebuds_backend.show_message(t("mgr_state_2"))
            return

        dev = self.applet.manager.device
        settings = self.applet.settings

        message = "{} ({})\n\n".format(settings.device_name, settings.address)
        message += "Model: {}\n".format(dev.get_property("device_model", "---"))
        message += "HW ver: {}\n".format(dev.get_property("device_ver", "---"))
        message += "FW ver: {}\n".format(dev.get_property("software_ver", "---"))
        message += "OTA ver: {}\n".format(dev.get_property("ota_version", "---"))
        message += "S/N: {}\n".format(dev.get_property("serial_number", "---"))
        message += "Headphone in: {}\n".format(dev.get_property("is_headphone_in", "---"))

        openfreebuds_backend.show_message(message)

    def do_unpair(self):
        self.applet.settings.address = ""
        self.applet.settings.device_name = ""
        self.applet.settings.write()

        self.applet.manager.unset_device(lock=False)
