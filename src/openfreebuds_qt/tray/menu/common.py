from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds
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

        self.settings_action: QAction | None = None
        self.change_device_action: QAction | None = None
        self.bugreport_action: QAction | None = None
        self.exit_action: QAction | None = None

    async def build(self):
        """
        Will rebuild entire tray menu. Should be called when something changes.
        """
        self.clear()

        await self.build_header()
        await self.build_main()
        await self.build_footer()

    async def build_header(self):
        """
        Will build common menu header with device name and (dis)connect button
        """
        state = await self.ofb.get_state()
        device_name, _ = await self.ofb.get_device_tags()

        if state != IOpenFreebuds.STATE_STOPPED:
            self.add_item(device_name, enabled=False)

        if state == IOpenFreebuds.STATE_CONNECTED:
            self.add_item(self.tr("Disconnect"), callback=self.do_disconnect)
        elif state == IOpenFreebuds.STATE_DISCONNECTED:
            self.add_item(self.tr("Connect"), callback=self.do_connect)

        self.addSeparator()

    @asyncSlot()
    async def do_disconnect(self):
        await self.ofb.run_shortcut("disconnect")

    @asyncSlot()
    async def do_connect(self):
        await self.ofb.run_shortcut("connect")

    @asyncSlot()
    async def do_exit(self):
        await self.root.exit(0)

    async def build_footer(self):
        """
        Will add common menu items, like settings, bugreport...
        """
        self.settings_action = self.add_item(self.tr("Settings..."))
        self.change_device_action = self.add_item(self.tr("Change device..."))
        self.bugreport_action = self.add_item(self.tr("Bugreport"))
        self.add_item(self.tr("Leave application"), callback=self.do_exit)

    async def build_main(self):
        """
        Override me
        """
        pass

    def add_item(self, text: str, callback: callable = None, enabled: bool = True):
        """
        One-call function to add new menu item
        """

        item = self.addAction(text)
        item.setEnabled(enabled)

        if callback:
            # noinspection PyUnresolvedReferences
            item.triggered.connect(callback)

        return item
