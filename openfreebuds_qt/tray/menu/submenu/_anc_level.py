from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.i18n_mappings import ANC_LEVEL_MAPPINGS
from openfreebuds_qt.tray.menu.generic import OfbTrayMenu


class OfbDeviceAncLevelTrayMenu(OfbTrayMenu):
    def __init__(self, parent: QWidget, ofb: IOpenFreebuds):
        super().__init__(parent, ofb)

        self.setTitle(self.tr("Intensity..."))
        self.anc_level_actions: dict[str, QAction] = {}
        for code in ANC_LEVEL_MAPPINGS:
            self._add_anc_level_option(code, ANC_LEVEL_MAPPINGS[code])

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

        self.anc_level_actions[code] = self.add_item(text=self.tr(display_name),
                                                     callback=_set_anc,
                                                     visible=False,
                                                     checked=False)
