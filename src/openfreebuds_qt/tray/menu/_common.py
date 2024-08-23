from typing import Optional

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu
from qasync import asyncSlot

from openfreebuds_qt.generic import IOfbQtMainWindow
from openfreebuds_qt.tray.generic import IOfbTrayIcon


class OfbCommonTrayMenu(QMenu):
    """
    Common OpenFreebuds tray menu parts
    """

    def __init__(self, root: IOfbQtMainWindow, tray: IOfbTrayIcon):
        super().__init__(root)

        self.root = root
        self.tray = tray
        self.ofb = root.ofb
        self._changed_prop = "", None

        # Placeholders for common items
        self.device_name_action: Optional[QAction] = None
        self.connect_action: Optional[QAction] = None
        self.header_separator: Optional[QAction] = None
        self.settings_action: Optional[QAction] = None
        self.change_device_action: Optional[QAction] = None
        self.bugreport_action: Optional[QAction] = None
        self.leave_action: Optional[QAction] = None

    def build_device_header(self, connection_state: Optional[bool] = None):
        self.device_name_action = self.add_item(text="OpenFreebuds",
                                                enabled=False,
                                                visible=False)

        if connection_state is True:
            self.connect_action = self.add_item(text=self.tr("Disconnect"),
                                                callback=self.do_disconnect)
        elif connection_state is False:
            self.connect_action = self.add_item(text=self.tr("Connect"),
                                                callback=self.do_connect)

        self.header_separator = self.addSeparator()

    def build_footer(self):
        self.settings_action = self.add_item(self.tr("Settings..."))
        self.change_device_action = self.add_item(self.tr("Change device..."))
        self.bugreport_action = self.add_item(self.tr("Bugreport"))
        self.leave_action = self.add_item(self.tr("Leave application"),
                                          callback=self.do_exit)

    async def on_attach(self):
        """
        Will refresh all properties in menu
        """

        if self.device_name_action:
            device_name, _ = await self.ofb.get_device_tags()
            self.device_name_action.setText(device_name)
            self.device_name_action.setVisible(True)

        self._changed_prop = "", None
        await self.update_items()

    async def on_core_property_change(self, group: str, prop: str = None, *_etc):
        """
        Will refresh items that depends on provided properties
        """
        self._changed_prop = group, prop
        await self.update_items()

    @asyncSlot()
    async def do_disconnect(self):
        await self.ofb.run_shortcut("disconnect")

    @asyncSlot()
    async def do_connect(self):
        await self.ofb.run_shortcut("connect")

    @asyncSlot()
    async def do_exit(self):
        await self.root.exit(0)

    def is_changed(self, group: str, prop: str = None):
        ch_group, ch_prop = self._changed_prop
        if ch_group == "":
            return True
        if ch_group == group and (prop is None or ch_prop is None or ch_prop == prop):
            return True
        return False

    def add_item(
            self,
            text: str,
            callback: callable = None,
            visible: bool = True,
            enabled: bool = True,
            checked: Optional[bool] = None,
    ):
        """
        One-call function to add new menu item
        """

        item = self.addAction(text)
        item.setEnabled(enabled)

        if not visible:
            item.setVisible(False)

        if checked is not None:
            item.setCheckable(True)
            item.setChecked(checked)

        if callback:
            # noinspection PyUnresolvedReferences
            item.triggered.connect(callback)

        return item

    async def update_items(self):
        """
        Override me
        """
        pass
