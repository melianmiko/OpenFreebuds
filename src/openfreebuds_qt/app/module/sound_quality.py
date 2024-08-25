from PyQt6.QtWidgets import QWidget, QComboBox
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.app.qt_utils import fill_combo_box
from openfreebuds_qt.designer.sound_quality import Ui_OfbQtSoundQualityModule
from openfreebuds_qt.i18n_mappings import EQ_PRESET_MAPPING


class OfbQtSoundQualityModule(Ui_OfbQtSoundQualityModule, OfbQtCommonModule):
    def __init__(self, parent: QWidget, ofb: IOpenFreebuds):
        super().__init__(parent)
        self.ofb = ofb
        self._eq_last_options: list[str] = []

        self.setupUi(self)

    def retranslate_ui(self):
        self.retranslateUi(self)

    async def update_ui(self, event: OfbCoreEvent):
        if event.is_changed("config", "sound_quality_preference"):
            value = await self.ofb.get_property("config", "sound_quality_preference")
            self.sq_root.setVisible(value is not None)
            if value == "sqp_connectivity":
                self.sq_radio_connection.setChecked(True)
            elif value == "sqp_quality":
                self.sq_radio_sound.setChecked(True)
            else:
                self.sq_radio_sound.setChecked(False)
                self.sq_radio_connection.setChecked(False)

        if event.is_changed("config", "equalizer_preset"):
            value = await self.ofb.get_property("config", "equalizer_preset")
            options = await self.ofb.get_property("config", "equalizer_preset_options")
            self.eq_root.setVisible(value is not None and options is not None)
            if options is not None:
                self._eq_last_options = list(options.split(","))
                fill_combo_box(self.eq_preset_box, self._eq_last_options, EQ_PRESET_MAPPING, value)

    @asyncSlot()
    async def on_sq_set_connectivity(self):
        await self.ofb.set_property("config", "sound_quality_preference", "sqp_connectivity")

    @asyncSlot()
    async def on_sq_set_quality(self):
        await self.ofb.set_property("config", "sound_quality_preference", "sqp_quality")

    @asyncSlot(int)
    async def on_eq_preset_change(self, index: int):
        value = self._eq_last_options[index]
        await self.ofb.set_property("config", "equalizer_preset", value)
