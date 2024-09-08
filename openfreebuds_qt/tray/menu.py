from typing import Optional

from PyQt6.QtGui import QAction
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds_backend.exception import OfbBackendDependencyMissingError
from openfreebuds_qt.tray.dialogs import OfbQtDependencyMissingDialog
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.generic import IOfbTrayIcon, IOfbQtApplication
from openfreebuds_qt.tray.menu_generic import OfbQtTrayMenuCommon
from openfreebuds_qt.tray.menu_anc_level import OfbDeviceAncLevelTrayMenu
from openfreebuds_qt.utils.report_tool import OfbQtReportTool


class OfbQtTrayMenu(OfbQtTrayMenuCommon):
    def __init__(self, tray: IOfbTrayIcon, context: IOfbQtApplication, ofb: IOpenFreebuds):
        super().__init__(context.main_window, ofb)

        self.ctx: IOfbQtApplication = context
        self.tray: IOfbTrayIcon = tray
        self.is_connected: bool = False
        self.first_time_render: bool = True

        # Translation data
        self.battery_option_names = {
            "left": self.tr("Left headphone:"),
            "right": self.tr("Right headphone:"),
            "case": self.tr("Battery case:"),
            "global": self.tr("Battery:"),
        }
        self.anc_mode_option_names = {
            "normal": self.tr("Disable noise control"),
            "cancellation": self.tr("Noise cancelling"),
            "awareness": self.tr("Awareness"),
        }

        # Header items
        self.device_name_action = self.add_item("OpenFreebuds",
                                                visible=False,
                                                enabled=False)
        self.disconnect_action = self.add_item(text=self.tr("Disconnect"),
                                               callback=self.do_disconnect,
                                               visible=False)
        self.connect_action = self.add_item(text=self.tr("Connect"),
                                            callback=self.do_connect,
                                            visible=False)
        self.add_separator()

        # Battery items
        self.battery_section = self.new_section()
        self.battery_is_tws: Optional[bool] = None
        self.battery_actions: dict[str, QAction] = {
            "left": self.add_item("", visible=False, enabled=False),
            "right": self.add_item("", visible=False, enabled=False),
            "case": self.add_item("", visible=False, enabled=False),
            "global": self.add_item("", visible=False, enabled=False),
        }
        self.add_separator()

        # ANC settings
        self.anc_section = self.new_section()
        self.anc_mode_actions: dict[str, QAction] = {}
        for code in self.anc_mode_option_names:
            self._add_anc_mode_option(code, self.anc_mode_option_names[code])
        self.anc_level_submenu = OfbDeviceAncLevelTrayMenu(self, ofb)
        self.anc_level_action = self.add_menu(self.anc_level_submenu)
        self.anc_level_action.setVisible(False)
        self.anc_separator = self.add_separator()

        # Footer
        self.footer_section = self.new_section()
        self.settings_action = self.add_item(self.tr("Settings..."),
                                             callback=self.do_settings)
        self.settings_action = self.add_item(self.tr("Bugreport..."),
                                             callback=self.do_bugreport)
        self.leave_action = self.add_item(self.tr("Leave application"),
                                          callback=self.do_exit)

    async def on_core_event(self, event: OfbCoreEvent):
        if event.kind_match(OfbEventKind.DEVICE_CHANGED):
            device_name, _ = await self.ofb.get_device_tags()
            self.device_name_action.setText(device_name)
            self.device_name_action.setVisible(True)

        if event.kind_match(OfbEventKind.STATE_CHANGED):
            state = await self.ofb.get_state()
            self.is_connected = state == IOpenFreebuds.STATE_CONNECTED

            self.connect_action.setVisible(state == IOpenFreebuds.STATE_DISCONNECTED)
            self.disconnect_action.setVisible(state == IOpenFreebuds.STATE_CONNECTED)
            self.set_section_visible(self.battery_section, state == IOpenFreebuds.STATE_CONNECTED)
            self.set_section_visible(self.anc_section, state == IOpenFreebuds.STATE_CONNECTED)

        if self.is_connected:
            if event.is_changed("battery", "") or self.first_time_render:
                battery = await self.ofb.get_property("battery")
                self.set_section_visible(self.battery_section, battery is not None)
                if battery is not None:
                    await self._update_battery(battery)

            if event.is_changed("anc") or self.first_time_render:
                anc = await self.ofb.get_property("anc")
                self.set_section_visible(self.anc_section, anc is not None)
                if anc is not None:
                    await self._update_anc(anc)

            self.first_time_render = False

    async def _update_battery(self, battery: dict):
        battery_is_tws = "case" in battery
        if battery_is_tws != self.battery_is_tws:
            self.battery_actions["left"].setVisible(battery_is_tws)
            self.battery_actions["right"].setVisible(battery_is_tws)
            self.battery_actions["case"].setVisible(battery_is_tws)
            self.battery_actions["global"].setVisible(not battery_is_tws)
            self.battery_is_tws = battery_is_tws

        for code in battery:
            if code in self.battery_actions:
                self.battery_actions[code].setText(
                    f"{self.battery_option_names[code]} {battery[code]}%"
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

    def _add_anc_mode_option(self, code: str, display_name: str):
        @asyncSlot()
        async def _set_anc(_):
            await self.ofb.set_property("anc", "mode", code)

        self.anc_mode_actions[code] = self.add_item(text=display_name,
                                                    callback=_set_anc,
                                                    visible=False,
                                                    checked=False)

    @asyncSlot()
    async def do_disconnect(self):
        try:
            await self.ofb.run_shortcut("disconnect", no_catch=True)
        except OfbBackendDependencyMissingError as e:
            await OfbQtDependencyMissingDialog(self.ctx, list(e.args)).get_user_response()

    @asyncSlot()
    async def do_connect(self):
        try:
            await self.ofb.run_shortcut("connect", no_catch=True)
        except OfbBackendDependencyMissingError as e:
            await OfbQtDependencyMissingDialog(self.ctx, list(e.args)).get_user_response()

    def do_settings(self):
        if self.ctx.isVisible():
            self.ctx.activateWindow()
        self.ctx.show()

    @asyncSlot()
    async def do_bugreport(self):
        await OfbQtReportTool(self.ctx).create_and_show()

    @asyncSlot()
    async def do_exit(self):
        await self.ctx.exit(0)