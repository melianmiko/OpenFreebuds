from PyQt6.QtWidgets import QWidget
from qasync import asyncSlot

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.generic import IOfbQtApplication
from openfreebuds_qt.qt_i18n import get_eq_preset_names
from openfreebuds_qt.tray.menu_generic import OfbQtTrayMenuCommon


log = create_logger("OfbDeviceEqualizerTrayMenu")


class OfbDeviceEqualizerTrayMenu(OfbQtTrayMenuCommon):
    def __init__(self, parent: QWidget, ctx: IOfbQtApplication):
        super().__init__(parent, ctx.ofb)

        self.setTitle(self.tr("Equalizer preset…"))
        self.eq_preset_names = get_eq_preset_names()

    async def update_ui(self):
        current = await self.ofb.get_property("sound", "equalizer_preset")
        options = await self.ofb.get_property("sound", "equalizer_preset_options")
        if options is None:
            return

        self.clear()
        for code in options.split(","):
            self._add_item(code, self.eq_preset_names.get(code, code), code == current)

    def _add_item(self, code: str, display_name: str, active: bool = False):
        @asyncSlot()
        async def set_mode(_):
            await self.ofb.set_property("sound", "equalizer_preset", code)
            await self.update_ui()

        self.add_item(text=display_name,
                      callback=set_mode,
                      visible=True,
                      checked=active)
