from typing import Optional

from PyQt6.QtGui import QAction
from qasync import asyncSlot

from openfreebuds_qt.generic import IOfbQtMainWindow
from openfreebuds_qt.i18n_mappings import ANC_MODE_MAPPINGS, BATTERY_PROP_MAPPINGS
from openfreebuds_qt.tray.generic import IOfbTrayIcon
from openfreebuds_qt.tray.menu._common import OfbCommonTrayMenu
from openfreebuds_qt.tray.menu.submenu import OfbDeviceAncLevelTrayMenu


class OfbDeviceOnlineTrayMenu(OfbCommonTrayMenu):
    def __init__(self, root: IOfbQtMainWindow, tray: IOfbTrayIcon):
        super().__init__(root, tray)

        self.build_device_header(True)

        # Battery items
        self.battery_is_tws: Optional[bool] = None
        self.battery_actions: dict[str, QAction] = {
            "left": self.add_item("", visible=False, enabled=False),
            "right": self.add_item("", visible=False, enabled=False),
            "case": self.add_item("", visible=False, enabled=False),
            "global": self.add_item("", visible=False, enabled=False),
        }
        self.addSeparator()

        # ANC items
        self.last_anc_mode: str = ""
        self.anc_mode_actions: dict[str, QAction] = {}
        for code in ANC_MODE_MAPPINGS:
            self._add_anc_mode_option(code, ANC_MODE_MAPPINGS[code])
        self.anc_level_submenu = OfbDeviceAncLevelTrayMenu(root, tray)
        self.anc_level_action = self.addMenu(self.anc_level_submenu)
        self.anc_level_action.setVisible(False)
        self.anc_separator = self.addSeparator()
        self.anc_separator.setVisible(False)

        # Footer
        self.build_footer()

    async def update_items(self):
        # Battery
        if self.is_changed("battery", ""):
            battery = await self.ofb.get_property("battery")
            if battery is not None:
                await self._update_battery(battery)

        # ANC modes
        if self.is_changed("anc"):
            anc = await self.ofb.get_property("anc")
            if anc is not None:
                await self._update_anc(anc)

    async def _update_battery(self, battery: dict):
        battery_is_tws = "case" in battery
        if battery_is_tws is not self.battery_is_tws:
            self.battery_actions["left"].setVisible(battery_is_tws)
            self.battery_actions["right"].setVisible(battery_is_tws)
            self.battery_actions["case"].setVisible(battery_is_tws)
            self.battery_actions["global"].setVisible(not battery_is_tws)

        for code in battery:
            if code in self.battery_actions:
                self.battery_actions[code].setText(
                    f"{self.tr(BATTERY_PROP_MAPPINGS[code])} {battery[code]}%"
                )

    async def _update_anc(self, anc: dict):
        mode = anc["mode"]
        mode_options = list(anc["mode_options"].split(","))
        for code in self.anc_mode_actions:
            self.anc_mode_actions[code].setVisible(code in mode_options)
            self.anc_mode_actions[code].setChecked(code == mode)

        if "level" in anc and "level_options" in anc:
            self.anc_level_action.setVisible(True)
            self.anc_level_submenu.on_update(anc)
        else:
            self.anc_level_action.setVisible(False)
        self.anc_separator.setVisible(True)

    def _add_anc_mode_option(self, code: str, display_name: str):
        @asyncSlot()
        async def _set_anc(_):
            await self.ofb.set_property("anc", "mode", code)

        self.anc_mode_actions[code] = self.add_item(text=self.tr(display_name),
                                                    callback=_set_anc,
                                                    visible=False,
                                                    checked=False)
