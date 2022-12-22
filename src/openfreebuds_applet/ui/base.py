import os

from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import updater, actions
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
        device_name = self.manager.device_name
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

    @utils.async_with_ui("DoConnect")
    def do_connect(self):
        actions.do_connect(self.manager)

    @utils.async_with_ui("DoDisconnect")
    def do_disconnect(self):
        actions.do_disconnect(self.manager)
