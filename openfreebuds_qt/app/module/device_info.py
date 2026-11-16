import re

from PyQt6.QtCore import QDateTime, QLocale
from PyQt6.QtWidgets import QTableWidgetItem

from openfreebuds import OfbEventKind
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.app.module.device_colors import (
    LEGACY_COLOR_ALIASES,
    translate_color_name,
    translate_model_name,
)
from openfreebuds_qt.utils.qt_utils import qt_error_handler
from openfreebuds_qt.designer.device_info import Ui_OfbQtDeviceInfoModule

# Protocol parameter number -> English source string, translated through the
# "OfbQtDeviceInfoModule" i18n context. Unlisted numbers report as Unknown Field.
FIELD_MEANING = {
    2: "Model",
    3: "Hardware version",
    7: "Software version",
    9: "Serial number",
    10: "Device submodel",
    15: "Device model",
    24: "Earbud serial number",
    25: "Color",
    "left_serial_number": "Left earbud serial number",
    "right_serial_number": "Right earbud serial number",
}

# Named keys produced by the driver, mapped back to their protocol number so the
# first column can always show the raw field id.
KEY_TO_NUMBER = {
    "hardware_ver": 3,
    "software_ver": 7,
    "serial_number": 9,
    "device_submodel": 10,
    "device_model": 15,
    "left_serial_number": 24,
    "right_serial_number": 24,
}


class OfbQtDeviceInfoModule(Ui_OfbQtDeviceInfoModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = OfbQtConfigParser.get_instance()
        self.setupUi(self)
        self.all_data_table.setColumnCount(3)
        self.all_data_table.setHorizontalHeaderLabels([
            self.tr("Field"),
            self.tr("Meaning"),
            self.tr("Value"),
        ])
        self.all_data_table.setColumnWidth(0, 60)
        self.all_data_table.setColumnWidth(1, 150)
        # Remove the automatic row number on the left; field number is data, not a row index
        self.all_data_table.verticalHeader().setVisible(False)

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

                title = _device_title(info)
                self.device_name.setText(title or _clean_model_name(device_name))

                rows = sorted(
                    ((code, value) for code, value in info.items() if not code.startswith("_")),
                    key=lambda item: _field_number(item[0]),
                )
                self.all_data_table.setRowCount(len(rows))
                for index, (code, value) in enumerate(rows):
                    localized = self._localize(code, value)
                    number = _field_number(code)
                    self.all_data_table.setItem(
                        index, 0, QTableWidgetItem("" if number == 99 else str(number)))
                    self.all_data_table.setItem(
                        index, 1, QTableWidgetItem(self._meaning(code)))
                    self.all_data_table.setItem(index, 2, QTableWidgetItem(localized or "--"))
                self.all_data_table.show()

    def _meaning(self, code: str) -> str:
        source = FIELD_MEANING.get(code)
        if not source:
            source = FIELD_MEANING.get(_field_number(code))
        if not source:
            return self.tr("Unknown Field")
        return self.tr(source)

    def _localize(self, code: str, value) -> str:
        if value is None:
            return ""
        text = value if isinstance(value, str) else str(value)
        if isinstance(value, (bytes, bytearray)):
            return value.hex(" ")
        if code == "field_2" or _field_number(code) == 2:
            # Model name: "HUAWEI FreeClip 2 S" -> localized marketing name
            localized = translate_model_name(text)
            return localized
        if code == "field_25" or _field_number(code) == 25:
            return _localize_color(text)
        return text


def _device_title(info: dict) -> str:
    """Build the "HUAWEI FreeClip 2 (Denim Blue)" title: localized model name plus the localized color from field_25. Chinese uses full-width brackets. The title contains no modelId or internal code, only the product name (color)."""
    color_value = info.get("field_25") or ""
    raw_model = info.get("field_2") or info.get("field_15") or info.get("device_model") or ""
    model_name = _clean_model_name(translate_model_name(raw_model))
    if not model_name:
        return ""

    color_name = _localize_color(color_value) if color_value else ""
    color_only = color_name.rpartition(" (")[0] if " (" in color_name else color_name
    if not color_only:
        return model_name

    if _has_cjk(color_only):
        return f"{model_name}（{color_only}）"
    return f"{model_name} ({color_only})"


def _clean_model_name(name: str) -> str:
    """Strip the internal name/ID from the model string, for example 'HUAWEI FreeClip 2 (ZAB2-L)'."""
    name = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]\s*$", "", name).strip()
    return name


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _field_number(code: str) -> int:
    if code in KEY_TO_NUMBER:
        return KEY_TO_NUMBER[code]
    if code.startswith("field_"):
        try:
            return int(code[6:])
        except ValueError:
            return 99
    return 99


def _localize_color(value: str) -> str:
    """
    Localize "Denim blue (05)" style values: translate the name part, keep the code.
    """
    name, separator, code = value.rpartition(" (")
    if not separator or not code.endswith(")"):
        return translate_color_name(value)
    localized = translate_color_name(name)
    if localized == name and name not in LEGACY_COLOR_ALIASES:
        return value
    return f"{localized} ({code[:-1]})"
