import os

from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import actions
from pystrayx import Menu


class QuitingMenu(Menu):
    """
    This menu will appear after clicking "Exit" action
    and will provide force quit option
    """

    # noinspection PyUnresolvedReferences,PyProtectedMember
    def on_build(self):
        self.add_item(t("Exiting..."), enabled=False)
        self.add_item(t("Force exit"), action=os._exit, args=[0])


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
        device_name = self.manager.device_name
        is_connected = self.manager.state == self.manager.STATE_CONNECTED

        self.add_updater()

        if self.manager.state != self.manager.STATE_NO_DEV:
            self.add_item(text=device_name, enabled=False)

            if is_connected:
                self.add_item(t('Disconnect'), self.do_disconnect)
            else:
                self.add_item(t('Connect'), self.do_connect)

        self.add_separator()

    def add_updater(self):
        # noinspection PyBroadException
        try:
            updater = self.applet.modules.modules["update_check"]
            has_update, new_version = updater.get_result()
            self.add_item(text=f"{t('Update OpenFreebuds')} ({new_version})",
                          action=updater.show_update_message,
                          visible=has_update)
        except Exception:
            pass

    @utils.async_with_ui("DoConnect")
    def do_connect(self):
        actions.do_connect(self.manager)

    @utils.async_with_ui("DoDisconnect")
    def do_disconnect(self):
        actions.do_disconnect(self.manager)
