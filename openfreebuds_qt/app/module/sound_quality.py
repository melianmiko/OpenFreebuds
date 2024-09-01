import logging

from qasync import asyncSlot

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.app.qt_utils import fill_combo_box
from openfreebuds_qt.designer.sound_quality import Ui_OfbQtSoundQualityModule
from openfreebuds_qt.i18n_mappings import EQ_PRESET_MAPPING

log = create_logger("OfbQtSoundQualityModule")


class OfbQtSoundQualityModule(Ui_OfbQtSoundQualityModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._eq_last_options: list[str] = []

        self.setupUi(self)

    def retranslate_ui(self):
        self.retranslateUi(self)

    async def update_ui(self, event: OfbCoreEvent):
        sound = await self.ofb.get_property("sound")
        self.list_item.setVisible(sound is not None)
        if sound is None:
            return

        if event.is_changed("sound", "quality_preference"):
            value = sound["quality_preference"]
            self.sq_root.setVisible(value is not None)
            if value == "sqp_connectivity":
                self.sq_radio_connection.setChecked(True)
            elif value == "sqp_quality":
                self.sq_radio_sound.setChecked(True)
            else:
                self.sq_radio_sound.setChecked(False)
                self.sq_radio_connection.setChecked(False)

        if event.is_changed("sound", "equalizer_preset"):
            value = sound["equalizer_preset"]
            options = sound["equalizer_preset_options"]
            self.eq_root.setVisible(value is not None and options is not None)
            if options is not None:
                self._eq_last_options = list(options.split(","))
                fill_combo_box(self.eq_preset_box, self._eq_last_options, EQ_PRESET_MAPPING, value)

    @asyncSlot()
    async def on_sq_set_connectivity(self):
        await self.ofb.set_property("sound", "quality_preference", "sqp_connectivity")

    @asyncSlot()
    async def on_sq_set_quality(self):
        await self.ofb.set_property("sound", "quality_preference", "sqp_quality")

    @asyncSlot(int)
    async def on_eq_preset_change(self, index: int):
        value = self._eq_last_options[index]
        await self.ofb.set_property("sound", "equalizer_preset", value)
