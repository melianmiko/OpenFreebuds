import json

from PyQt6.QtWidgets import QWidget
from qasync import asyncSlot

from openfreebuds_qt.generic import IOfbQtApplication
from openfreebuds_qt.tray.menu_generic import OfbQtTrayMenuCommon


class OfbDeviceDualConnectTrayMenu(OfbQtTrayMenuCommon):
    def __init__(self, parent: QWidget, ctx: IOfbQtApplication):
        super().__init__(parent, ctx.ofb)

        self.setTitle(self.tr("Dual-connect..."))

    async def update_ui(self):
        data = await self.ofb.get_property("dual_connect")
        if not data or "devices" not in data:
            return

        self.clear()
        for addr, data in json.loads(data["devices"]).items():
            self._add_item(addr, data["name"], data["connected"])

    def _add_item(self, addr: str, display_name: str, active: bool = False):
        @asyncSlot()
        async def toggle(_):
            await self.ofb.set_property("dual_connect", f"{addr}:connected", json.dumps(not active))
            await self.update_ui()

        self.add_item(text=display_name,
                      callback=toggle,
                      visible=True,
                      checked=active)
