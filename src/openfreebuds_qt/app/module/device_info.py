from PyQt6.QtWidgets import QWidget, QTableWidgetItem

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.designer.device_info import Ui_OfbQtDeviceInfoModule


class OfbQtDeviceInfoModule(Ui_OfbQtDeviceInfoModule, OfbQtCommonModule):
    def __init__(self, parent: QWidget, ofb: IOpenFreebuds):
        super().__init__(parent)
        self.ofb = ofb

        self.setupUi(self)

    def retranslate_ui(self):
        self.retranslateUi(self)

    async def update_ui(self, event: OfbCoreEvent):
        if event.is_changed("info") or event.kind_match("device_changed"):
            device_name, device_address = await self.ofb.get_device_tags()
            info: dict[str, str] = await self.ofb.get_property("info")
            if info is None:
                return

            self.device_address.setText(device_address)
            self.device_name.setText(device_name)
            self.device_firmware.setText(info.get("software_ver", "--"))

            self.all_data_table.clearContents()
            self.all_data_table.setRowCount(len(info.keys()))
            for index, (code, value) in enumerate(info.items()):
                self.all_data_table.setItem(index, 0, QTableWidgetItem(code))
                self.all_data_table.setItem(index, 1, QTableWidgetItem(value))
            self.all_data_table.show()
