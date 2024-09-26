import json

from PIL import ImageQt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QListWidgetItem, QMessageBox
from qasync import asyncSlot

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.utils import blocked_signals, exec_msg_box_async, qt_error_handler, format_mac_address
from openfreebuds_qt.designer.dual_connect import Ui_OfbQtDualConnectModule
from openfreebuds_qt.utils.icon import create_dual_connect_icon

log = create_logger("OfbQtDualConnectModule")


class OfbQtDualConnectModule(Ui_OfbQtDualConnectModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_index: int = -1
        self._all_data: list[tuple[str, dict]] = []

        self.setupUi(self)

    async def update_ui(self, event: OfbCoreEvent):
        async with qt_error_handler("OfbQtDualConnectModule_UpdateUi", self.ctx):
            # Setup visibility
            data = await self.ofb.get_property("dual_connect")
            self.list_item.setVisible(data is not None)
            if not data or "devices" not in data:
                return

            # Setup global toggle
            if event.is_changed("dual_connect", "enabled"):
                with blocked_signals(self.global_toggle):
                    self.global_toggle.setChecked(data.get("enabled") == "true")

            if not event.is_changed("dual_connect", "devices") \
                    and not event.is_changed("dual_connect", "preferred_device"):
                return

            # Setup devices list
            self._all_data = []
            self.devices_list.clear()
            for addr, data in json.loads(data["devices"]).items():
                icon = create_dual_connect_icon(is_connected=data["connected"],
                                                is_playing=data["playing"],
                                                is_primary=data["preferred"])
                self.devices_list.addItem(
                    QListWidgetItem(QIcon(ImageQt.toqpixmap(icon)), data["name"])
                )
                self._all_data.append((addr, data))

            # Setup/recover selected device
            if self._current_index == -1:
                self.devices_list.setCurrentRow(0)
            else:
                self.devices_list.setCurrentRow(self._current_index)

            self.button_toggle_connect.setEnabled(True)
            self.current_device_auto_connect.setEnabled(True)
            self.current_device_prefered.setEnabled(True)
            self.refresh_button.setEnabled(True)

    @asyncSlot()
    async def on_connect_toggle(self):
        async with qt_error_handler("OfbQtDualConnectModule_ToggleConnect", self.ctx):
            addr, data = self._all_data[self._current_index]

            self.button_toggle_connect.setEnabled(False)
            await self.ofb.set_property(
                "dual_connect",
                f"{addr}:connected",
                json.dumps(not data["connected"])
            )

    def _update_current_device_view(self, addr: str, data: dict):
        self.current_device_name.setText(data['name'])
        self.current_device_address.setText(format_mac_address(addr))
        with blocked_signals(self.current_device_prefered):
            self.current_device_prefered.setChecked(data["preferred"])
        with blocked_signals(self.current_device_auto_connect):
            self.current_device_auto_connect.setEnabled(data.get("auto_connect") is not None)
            self.current_device_auto_connect.setChecked(data.get("auto_connect") or False)

        self.button_toggle_connect.setText(
            self.tr("Disconnect") if data["connected"] else self.tr("Connect")
        )

    @asyncSlot(bool)
    async def on_set_preferred(self, state: bool):
        async with qt_error_handler("OfbQtDualConnectModule_SetPreferred", self.ctx):
            addr = "000000000000" if not state else self._all_data[self._current_index][0]
            self.current_device_prefered.setEnabled(False)
            await self.ofb.set_property("dual_connect", "preferred_device", addr)

    @asyncSlot(bool)
    async def on_set_auto_connect(self, state: bool):
        async with qt_error_handler("OfbQtDualConnectModule_AutoConnect", self.ctx):
            addr = self._all_data[self._current_index][0]
            self.current_device_auto_connect.setEnabled(False)
            await self.ofb.set_property("dual_connect", f"{addr}:auto_connect",
                                        json.dumps(state))

    @asyncSlot(int)
    async def on_device_select(self, index: int):
        if index == self._current_index:
            return

        addr, data = self._all_data[index]
        self._current_index = index
        self._update_current_device_view(addr, data)

    @asyncSlot()
    async def on_refresh(self):
        self.refresh_button.setEnabled(False)
        await self.ofb.set_property("dual_connect", "refresh", "1")

    @asyncSlot()
    async def on_set_global_toggle(self):
        async with qt_error_handler("OfbQtDualConnectModule_GlobalToggle", self.ctx):
            await self.ofb.set_property("dual_connect", "enabled", json.dumps(self.global_toggle.isChecked()))

    @asyncSlot()
    async def on_unpair(self):
        async with qt_error_handler("OfbQtDualConnectModule_Unpair", self.ctx):
            addr, data = self._all_data[self._current_index]
            box = QMessageBox(
                QMessageBox.Icon.Question,
                self.tr("Unpair device"),
                self.tr("Do you really want to unpair %1 from your headphones?").replace("%1", data["name"]),
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                self
            )
            box.setModal(True)
            if await exec_msg_box_async(box) == QMessageBox.StandardButton.Ok:
                await self.ofb.set_property("dual_connect", f"{addr}:name", "")
