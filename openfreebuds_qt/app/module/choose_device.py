import asyncio
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem
from qasync import asyncSlot

from openfreebuds import is_device_supported, OfbEventKind
from openfreebuds_backend import bt_list_devices
from openfreebuds_qt.utils.device_auto_select import OfbQtDeviceAutoSelect
from openfreebuds_qt.app.dialog.manual_connect import OfbQtManualConnectDialog
from openfreebuds_qt.app.dialog.porifle_picker import OfbQtProfilePickerDialog
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.utils.qt_utils import qt_error_handler
from openfreebuds_qt.config.main import OfbQtConfigParser
from openfreebuds_qt.designer.module_device_select import Ui_OfbQtDeviceSelectModule


class OfbQtChooseDeviceModule(Ui_OfbQtDeviceSelectModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = OfbQtConfigParser.get_instance()
        self.setupUi(self)

        self._connect_task: Optional[asyncio.Task] = None

    async def update_ui(self, event: OfbCoreEvent):
        async with qt_error_handler("OfbQtChooseDeviceModule_UpdateUi", self.ctx):
            if event.kind_match(OfbEventKind.DEVICE_CHANGED):
                is_auto_config = self.config.get("device", "auto_setup", True)
                self.manual_setup_root.setVisible(not is_auto_config)
                self.auto_setup_root.setVisible(is_auto_config)
                self.auto_config_checkbox.setChecked(is_auto_config)
                await self._update_list()

    @asyncSlot()
    async def on_refresh_list(self):
        async with qt_error_handler("OfbQtChooseDeviceModule_ManualRefresh", self.ctx):
            await self._update_list()

    async def _update_list(self):
        device_name, device_addr = await self.ofb.get_device_tags()
        results = await bt_list_devices()
        self.paired_list.clear()
        for row in results:
            entry = QListWidgetItem(row["name"], self.paired_list)
            checked = row["address"] == device_addr
            entry.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            entry.setData(Qt.ItemDataRole.UserRole, row["address"])

            self.paired_list.addItem(entry)

    @asyncSlot(QListWidgetItem)
    async def on_device_select(self, item: QListWidgetItem):
        async with qt_error_handler("OfbQtChooseDeviceModule_SelectDevice", self.ctx):
            address = item.data(Qt.ItemDataRole.UserRole)
            name = item.text()

            if not is_device_supported(name):
                result, name = await OfbQtProfilePickerDialog(self).get_user_response()
                if not result:
                    return

            # noinspection PyAsyncCall
            self._connect_task = asyncio.create_task(
                self.ofb.start(name, address)
            )
            self.config.set_device_data(name, address)
            self.config.save()
            await asyncio.sleep(0.5)
            await self._update_list()

    @asyncSlot()
    async def on_manual_config(self):
        async with qt_error_handler("OfbQtChooseDeviceModule_ManualSetup", self.ctx):
            result, name, address = await OfbQtManualConnectDialog(self).get_user_response()
            if not result:
                return

            await self.ofb.start(name, address)
            self.config.set_device_data(name, address)
            self.config.save()

    @asyncSlot(bool)
    async def on_auto_config_toggle(self, value):
        async with qt_error_handler("OfbQtChooseDeviceModule_AutoConfigToggle", self.ctx):
            self.config.set("device", "auto_setup", value)
            self.config.save()
            await self.update_ui(OfbCoreEvent(None, []))

            if value is True:
                await OfbQtDeviceAutoSelect.trigger(self.ofb)
