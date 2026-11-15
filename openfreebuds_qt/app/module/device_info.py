from PyQt6.QtCore import QDateTime, QLocale
from PyQt6.QtWidgets import QTableWidgetItem

from openfreebuds import OfbEventKind
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.app.module.device_colors import translate_color_name
from openfreebuds_qt.utils.qt_utils import qt_error_handler
from openfreebuds_qt.designer.device_info import Ui_OfbQtDeviceInfoModule


class OfbQtDeviceInfoModule(Ui_OfbQtDeviceInfoModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = OfbQtConfigParser.get_instance()
        self.setupUi(self)

    async def update_ui(self, event: OfbCoreEvent):
        async with qt_error_handler("OfbQtDeviceInfoModule_UpdateUi", self.ctx):
            if event.is_changed("info") or event.kind_match(OfbEventKind.DEVICE_CHANGED):
                device_name, device_address = await self.ofb.get_device_tags()
                info: dict[str, str] = await self.ofb.get_property("info")

                last_charged = self.config.get("last_charged", device_address, 0)
                if last_charged == 0:
                    self.last_charged_field.setText(self.tr("Unknown"))
                else:
                    date = QDateTime.fromSecsSinceEpoch(int(last_charged))
                    self.last_charged_field.setText(
                        QLocale.system().toString(date, QLocale.FormatType.LongFormat)
                    )

                self.device_address.setText(device_address)
                self.device_name.setText(device_name)
                self.all_data_table.clearContents()

                if info is None:
                    return

                self.device_firmware.setText(info.get("software_ver", "--"))
                self.device_internal_name.setText(info.get("_internal_name") or "--")
                self.device_product_id.setText(info.get("_product_id") or "--")

                rows = [(code, value) for code, value in info.items() if not code.startswith("_")]
                self.all_data_table.setRowCount(len(rows))
                for index, (code, value) in enumerate(rows):
                    if code == "field_25":
                        value = _localize_value(value)
                    self.all_data_table.setItem(index, 0, QTableWidgetItem(code))
                    self.all_data_table.setItem(index, 1, QTableWidgetItem(value))
                self.all_data_table.show()


def _localize_value(value: str) -> str:
    """
    Translate the color name part of "Name (Code)" values.
    """
    name, separator, code = value.rpartition(" (")
    if not separator or not code.endswith(")"):
        return value
    localized = translate_color_name(name)
    if localized == name:
        return value
    return f"{localized} ({code[:-1]})"
