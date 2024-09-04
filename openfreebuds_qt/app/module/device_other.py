import json

from qasync import asyncSlot

from openfreebuds import OfbEventKind
from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.app.qt_utils import blocked_signals, qt_error_handler
from openfreebuds_qt.designer.device_other import Ui_OfbQtDeviceOtherSettingsModule

LANGUAGE_OPTION_MAPPING = {
    "en-GB": "English (British)",
    "zh-CN": "Chinese"
}


class OfbQtDeviceOtherSettingsModule(Ui_OfbQtDeviceOtherSettingsModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lang_options: list[str] = []

        self.setupUi(self)

    async def update_ui(self, event: OfbCoreEvent):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_UpdateUi", self.ctx):
            if event.kind_match(OfbEventKind.DEVICE_CHANGED):
                # Visibility setup
                auto_pause_visible = await self.ofb.get_property("config", "auto_pause") is not None
                low_latency_visible = await self.ofb.get_property("config", "low_latency") is not None
                service_language_visible = await self.ofb.get_property("service", "language") is not None

                self.auto_pause_root.setVisible(auto_pause_visible)
                self.low_latency_root.setVisible(low_latency_visible)
                self.service_language_root.setVisible(service_language_visible)

                self.list_item.setVisible(auto_pause_visible or service_language_visible or low_latency_visible)

            if event.is_changed("config", "auto_pause"):
                with blocked_signals(self.auto_pause_toggle):
                    self.auto_pause_toggle.setChecked(await self.ofb.get_property("config", "auto_pause") == "true")

            if event.is_changed("config", "low_latency"):
                with blocked_signals(self.low_latency_toggle):
                    self.low_latency_toggle.setChecked(await self.ofb.get_property("config", "low_latency") == "true")
                    self.low_latency_toggle.setEnabled(True)

            if event.is_changed("service", "language_options"):
                options = await self.ofb.get_property("service", "language_options")
                if options is not None:
                    self.lang_options = options.split(",")
                    with blocked_signals(self.service_language_box):
                        self.service_language_box.clear()
                        self.service_language_box.addItems(
                            [LANGUAGE_OPTION_MAPPING.get(o, o) for o in self.lang_options]
                        )
                        self.service_language_box.setCurrentIndex(-1)

    def retranslate_ui(self):
        self.retranslateUi(self)

    @asyncSlot(bool)
    async def on_low_latency_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetLowLatency", self.ctx):
            self.low_latency_toggle.setEnabled(False)
            await self.ofb.set_property("config", "low_latency", json.dumps(value))

    @asyncSlot(bool)
    async def on_auto_pause_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetAutoPause", self.ctx):
            await self.ofb.set_property("config", "auto_pause", json.dumps(value))

    @asyncSlot(int)
    async def on_language_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetLanguage", self.ctx):
            await self.ofb.set_property("service", "language", self.lang_options[index])
