import asyncio
import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSlider, QSpacerItem
from qasync import asyncSlot

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.utils.qt_utils import fill_combo_box, blocked_signals
from openfreebuds_qt.designer.sound_quality import Ui_OfbQtSoundQualityModule

log = create_logger("OfbQtSoundQualityModule")


class OfbQtSoundQualityModule(Ui_OfbQtSoundQualityModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.eq_preset_option_names = {
            "equalizer_preset_default": self.tr("Default"),
            "equalizer_preset_hardbass": self.tr("Bass-boost"),
            "equalizer_preset_treble": self.tr("Treble-boost"),
            "equalizer_preset_voices": self.tr("Voices"),
        }

        self._eq_last_options: list[str] = []

        self.setupUi(self)
        self._eq_rows: list[QSlider] = []
        self._last_preset_data: list[int] = []
        for i in range(10):
            self._add_slider(i)

    def _add_slider(self, i):
        lock = asyncio.Lock()

        @asyncSlot(int)
        async def _on_change(value: int):
            if lock.locked():
                return
            async with lock:
                self._last_preset_data[i] = value
                await self.ofb.set_property("sound", "equalizer_rows",
                                            json.dumps(self._last_preset_data))

        slider = QSlider(Qt.Orientation.Vertical, self.custom_eq_rows)
        slider.setRange(-60, 60)
        slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        slider.setTickInterval(5)
        slider.setToolTip("0")
        # noinspection PyUnresolvedReferences
        slider.valueChanged.connect(_on_change)
        self.custom_eq_rows_layout.addWidget(slider)
        self._eq_rows.append(slider)

    def retranslate_ui(self):
        self.retranslateUi(self)

    async def update_ui(self, event: OfbCoreEvent):
        sound = await self.ofb.get_property("sound")
        self.list_item.setVisible(sound is not None)
        if sound is None:
            return

        self.eq_custom_buttons.setVisible("equalizer_rows" in sound)

        if event.is_changed("sound", "quality_preference"):
            value = sound.get("quality_preference")
            self.sq_root.setVisible(value is not None)
            if value == "sqp_connectivity":
                self.sq_radio_connection.setChecked(True)
            elif value == "sqp_quality":
                self.sq_radio_sound.setChecked(True)
            else:
                self.sq_radio_sound.setChecked(False)
                self.sq_radio_connection.setChecked(False)

        if event.is_changed("sound", "equalizer_preset"):
            value = sound.get("equalizer_preset")
            options = sound.get("equalizer_preset_options")
            self.eq_root.setVisible(value is not None and options is not None)
            if options is not None:
                self._eq_last_options = list(options.split(","))
                fill_combo_box(self.eq_preset_box, self._eq_last_options, self.eq_preset_option_names, value)

        if event.is_changed("sound", "equalizer_rows"):
            rows = json.loads(sound.get("equalizer_rows") or "null")
            self.custom_eq_rows.setVisible(rows is not None)
            if rows is not None:
                self._last_preset_data = rows
                for i, value in enumerate(rows):
                    with blocked_signals(self._eq_rows[i]):
                        self._eq_rows[i].setValue(value)
                        self._eq_rows[i].setToolTip(str(value))

    @asyncSlot()
    async def on_new_preset(self):
        pass

    @asyncSlot()
    async def on_delete_preset(self):
        pass

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
