from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.qt_i18n import get_anc_level_names
from openfreebuds_qt.tray.menu_generic import OfbQtTrayMenuCommon


class OfbDeviceAncLevelTrayMenu(OfbQtTrayMenuCommon):
    def __init__(self, parent: QWidget, ofb: IOpenFreebuds):
        super().__init__(parent, ofb)

        self.anc_level_option_names = get_anc_level_names()

        self.setTitle(self.tr("Intensity…"))
        self.anc_level_actions: dict[str, QAction] = {}
        for code in self.anc_level_option_names:
            self._add_anc_level_option(code, self.anc_level_option_names[code])

    def on_update(self, anc):
        level = anc["level"]
        level_options = list(anc["level_options"].split(","))

        for code in self.anc_level_actions:
            self.anc_level_actions[code].setVisible(code in level_options)
            self.anc_level_actions[code].setChecked(code == level)

    def _add_anc_level_option(self, code: str, display_name: str):
        @asyncSlot()
        async def _set_anc(_):
            await self.ofb.set_property("anc", "level", code)

        self.anc_level_actions[code] = self.add_item(text=display_name,
                                                     callback=_set_anc,
                                                     visible=False,
                                                     checked=False)
