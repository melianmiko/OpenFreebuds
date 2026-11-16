from datetime import datetime

from PyQt6.QtGui import QAction
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.utils.stupid_rpc import RemoteError
from openfreebuds_backend.exception import OfbBackendDependencyMissingError
from openfreebuds_qt.app.dialog.error_dialog import OfbQtErrorDialog
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.generic import IOfbTrayIcon, IOfbQtApplication
from openfreebuds_qt.tray.battery import battery_levels, battery_menu_text
from openfreebuds_qt.tray.dialogs import OfbQtDependencyMissingDialog
from openfreebuds_qt.tray.menu_anc_level import OfbDeviceAncLevelTrayMenu
from openfreebuds_qt.tray.menu_dual_connect import OfbDeviceDualConnectTrayMenu
from openfreebuds_qt.tray.menu_equalizer import OfbDeviceEqualizerTrayMenu
from openfreebuds_qt.tray.menu_generic import OfbQtTrayMenuCommon
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.utils.report_tool import OfbQtReportTool

log = create_logger("OfbQtTrayMenu")


class OfbQtTrayMenu(OfbQtTrayMenuCommon):
    def __init__(self, tray: IOfbTrayIcon, context: IOfbQtApplication, ofb: IOpenFreebuds):
        super().__init__(context.main_window, ofb)

        self.ctx: IOfbQtApplication = context
        self.tray: IOfbTrayIcon = tray
        self.config = OfbQtConfigParser.get_instance()
        self.is_connected: bool = False
        self.first_time_render: bool = True
        self.device_mac_address: str = ""

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
        self.add_separator()

        # Extras
        self.new_section()
        self.add_item(self.tr("Settings…"), callback=self.do_settings)
        self.equalizer_submenu = OfbDeviceEqualizerTrayMenu(self, self.ctx)
        self.equalizer_action = self.add_menu(self.equalizer_submenu)
        self.dual_connect_submenu = OfbDeviceDualConnectTrayMenu(self, self.ctx)
        self.dual_connect_action = self.add_menu(self.dual_connect_submenu)
        self.add_separator()

        # Footer
        self.new_section()
        self.add_item(self.tr("Bugreport…"), callback=self.do_bugreport)
        self.add_item(self.tr("Leave application"), callback=self.do_exit)

    async def on_core_event(self, event: OfbCoreEvent, state: int):
        device_changed = event.kind_match(OfbEventKind.DEVICE_CHANGED)
        if device_changed:
            self._reset_device_state()
            self.first_time_render = True

        if device_changed or event.kind_in([OfbEventKind.STATE_CHANGED, OfbEventKind.QT_SETTINGS_CHANGED]):
            self.is_connected = state == IOpenFreebuds.STATE_CONNECTED

            device_name, device_addr = await self.ofb.get_device_tags()
            self.device_name_action.setVisible(device_name != "")
            self.device_name_action.setText(device_name)
            self.device_mac_address = device_addr

            self.connect_action.setVisible(state == IOpenFreebuds.STATE_DISCONNECTED)
            self.disconnect_action.setVisible(self.is_connected)
            self.set_section_visible(self.battery_section, self.is_connected)
            self.set_section_visible(self.anc_section, self.is_connected)
            self.equalizer_action.setVisible(
                self.is_connected
                and self.config.get("ui", "tray_show_equalizer", False)
                and await self.ofb.get_property("sound", "equalizer_preset", None) is not None
            )
            self.dual_connect_action.setVisible(
                self.is_connected
                and self.config.get("ui", "tray_show_dual_connect", False)
                and await self.ofb.get_property("dual_connect", "preferred_device", None) is not None
            )

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
                else:
                    self.anc_level_action.setVisible(False)
                    for action in self.anc_mode_actions.values():
                        action.setVisible(False)

            if event.is_changed("sound") or self.first_time_render:
                await self.equalizer_submenu.update_ui()

            if event.is_changed("dual_connect") or self.first_time_render:
                await self.dual_connect_submenu.update_ui()

            self.first_time_render = False

    def _reset_device_state(self):
        """Hide cached device-specific actions before the next device is read."""
        self.first_time_render = True
        self.set_section_visible(self.battery_section, False)
        self.set_section_visible(self.anc_section, False)
        self.equalizer_action.setVisible(False)
        self.dual_connect_action.setVisible(False)
        self.anc_level_action.setVisible(False)
        for action in self.anc_mode_actions.values():
            action.setVisible(False)
        self.equalizer_submenu.clear()
        self.dual_connect_submenu.clear()

    async def _update_battery(self, battery: dict):
        battery_is_tws = "case" in battery
        self.battery_actions["left"].setVisible(battery_is_tws)
        self.battery_actions["right"].setVisible(battery_is_tws)
        self.battery_actions["case"].setVisible(battery_is_tws)
        self.battery_actions["global"].setVisible(not battery_is_tws)

        # Update menu items
        levels = battery_levels(battery)
        for code, level in levels.items():
            if code in self.battery_actions:
                self.battery_actions[code].setText(
                    f"{self.battery_option_names[code]} "
                    f"{battery_menu_text(level, self.tr('Not connected'))}"
                )

        # Update last charged config field
        global_battery = battery.get("global", 0)
        last_charged = self.config.get("last_charged", self.device_mac_address, 0)
        if global_battery > 95 and datetime.now().timestamp() > last_charged + 3600:
            self.config.set("last_charged", self.device_mac_address, datetime.now().timestamp())
            self.config.save()

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

    async def _handle_shortcut_error(self, error: Exception):
        """Report a tray action failure without tearing down the application.

        RPC calls wrap server exceptions in RemoteError, so a dependency missing on
        the manager side arrives as RemoteError(class_name=...). Match that too.
        """
        dependency = isinstance(error, OfbBackendDependencyMissingError) or (
            isinstance(error, RemoteError)
            and error.class_name == "OfbBackendDependencyMissingError"
        )
        if dependency and len(error.args) >= 2:
            await OfbQtDependencyMissingDialog(self, list(error.args)).get_user_response()
            return

        log.exception("Tray shortcut failed", exc_info=error)
        await OfbQtErrorDialog(self.ctx.main_window).get_user_response(str(error))

    @asyncSlot()
    async def do_disconnect(self):
        try:
            await self.ofb.run_shortcut("disconnect", no_catch=True)
        except Exception as e:
            await self._handle_shortcut_error(e)

    @asyncSlot()
    async def do_connect(self):
        try:
            await self.ofb.run_shortcut("connect", no_catch=True)
        except Exception as e:
            await self._handle_shortcut_error(e)

    def do_settings(self):
        if self.ctx.main_window.isVisible():
            self.ctx.main_window.activateWindow()
        self.ctx.main_window.show()

    @asyncSlot()
    async def do_bugreport(self):
        await OfbQtReportTool(self.ctx).create_and_show()

    @asyncSlot()
    async def do_exit(self):
        await self.ctx.exit(0)
