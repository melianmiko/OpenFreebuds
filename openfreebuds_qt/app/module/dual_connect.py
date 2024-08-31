import json

from PIL import ImageQt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QListWidgetItem, QMessageBox, QCheckBox
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.app.qt_utils import blocked_signals, exec_msg_box_async, qt_error_handler
from openfreebuds_qt.data_format import format_mac_address
from openfreebuds_qt.designer.dual_connect import Ui_OfbQtDualConnectModule
from openfreebuds_qt.icon import create_dual_connect_icon

log = create_logger("OfbQtDualConnectModule")


class OfbQtDualConnectModule(Ui_OfbQtDualConnectModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_index: int = -1
        self._all_data: list[tuple[str, dict]] = []

        self.setupUi(self)

    def retranslate_ui(self):
        self.retranslateUi(self)

    async def update_ui(self, event: OfbCoreEvent):
        async with qt_error_handler("OfbQtDualConnectModule_UpdateUi", self.ctx):
            # Setup visibility depending on device modules
            if event.kind_match(OfbEventKind.STATE_CHANGED):
                state = await self.ofb.get_state()
                if state == IOpenFreebuds.STATE_CONNECTED:
                    available = await self.ofb.get_property("config", "dual_connect")
                    self.list_item.setVisible(available is not None)

            # Setup global toggle
            if event.is_changed("config", "dual_connect"):
                with blocked_signals(self.global_toggle):
                    self.global_toggle.setChecked(
                        await self.ofb.get_property("config", "dual_connect") == "true"
                    )

            # Setup devices list
            if not event.is_changed("dual_connect_devices"):
                return

            self._all_data = []
            self.devices_list.clear()
            devices = await self.ofb.get_property("dual_connect_devices")
            if devices is None:
                return

            for addr, data_raw in devices.items():
                data = json.loads(data_raw)
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
            self.refresh_button.setEnabled(True)

    @asyncSlot()
    async def on_connect_toggle(self):
        async with qt_error_handler("OfbQtDualConnectModule_ToggleConnect", self.ctx):
            addr, data = self._all_data[self._current_index]

            try:
                self.button_toggle_connect.setEnabled(False)
                await self.ofb.set_property(
                    "dual_connect_devices",
                    f"{addr}:connected",
                    json.dumps(not data["connected"])
                )
            except Exception:
                log.exception(f"Trying to switch connection state of {addr}")
                self.button_toggle_connect.setEnabled(True)

    def _update_current_device_view(self, addr: str, data: dict):
        self.current_device_name.setText(data['name'])
        self.current_device_address.setText(format_mac_address(addr))
        with blocked_signals(self.current_device_prefered):
            self.current_device_prefered.setChecked(data["preferred"])
        self.button_toggle_connect.setText(self.tr("Disconnect" if data["connected"] else "Connect"))

    @asyncSlot(bool)
    async def on_set_preferred(self, state: bool):
        addr = "000000000000" if not state else self._all_data[self._current_index][0]
        await self.ofb.set_property("config", "preferred_device", addr)

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
        await self.ofb.set_property("dual_connect_devices", "refresh", "1")

    @asyncSlot()
    async def on_set_global_toggle(self):
        async with qt_error_handler("OfbQtDualConnectModule_GlobalToggle", self.ctx):
            await self.ofb.set_property("config", "dual_connect", json.dumps(self.global_toggle.isChecked()))

    @asyncSlot()
    async def on_unpair(self):
        async with qt_error_handler("OfbQtDualConnectModule_Unpair", self.ctx):
            addr, data = self._all_data[self._current_index]
            box = QMessageBox(
                QMessageBox.Icon.Question,
                self.tr("Unpair device"),
                self.tr("Do you really want to unpair {} from your headphones?").format(data["name"]),
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                self
            )
            box.setModal(True)
            if await exec_msg_box_async(box) == QMessageBox.StandardButton.Ok:
                await self.ofb.set_property("dual_connect_devices", f"{addr}:name", "")
