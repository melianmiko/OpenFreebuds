import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)
from qasync import asyncSlot

from openfreebuds import OfbEventKind
from openfreebuds.driver.huawei.handler.prompt_tone import PROMPT_TONES
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.qt_i18n import get_prompt_tone_names
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.utils.qt_utils import blocked_signals, qt_error_handler


class OfbQtCaseSoundModule(OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setObjectName("OfbQtCaseSoundModule")
        self.tone_values = [str(tone.tone_id) for tone in PROMPT_TONES]
        self.prompt_tone_names = get_prompt_tone_names()

        self.root_layout = QVBoxLayout(self)
        self.group = QGroupBox(self.tr("Charging case sounds"), self)
        self.grid = QGridLayout(self.group)
        self.grid.setColumnStretch(1, 1)

        self.enabled_toggle = QCheckBox(self.tr("Opening sound"), self.group)
        self.grid.addWidget(self.enabled_toggle, 0, 0, 1, 2)

        self.grid.addWidget(QLabel(self.tr("Sound"), self.group), 1, 0)
        self.tone_box = QComboBox(self.group)
        for tone in PROMPT_TONES:
            self.tone_box.addItem(self.prompt_tone_names.get(tone.name, tone.name.replace("_", " ")))
        self.grid.addWidget(self.tone_box, 1, 1)

        self.grid.addWidget(QLabel(self.tr("Volume"), self.group), 2, 0)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal, self.group)
        self.volume_slider.setRange(0, 15)
        self.volume_slider.setTickInterval(1)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_label = QLabel("0", self.group)
        self.grid.addWidget(self.volume_slider, 2, 1)
        self.grid.addWidget(self.volume_label, 2, 2)

        self.prepare_button = QPushButton(self.tr("Download all sounds"), self.group)
        self.status_label = QLabel(self.tr("Idle"), self.group)
        self.grid.addWidget(self.prepare_button, 3, 0)
        self.grid.addWidget(self.status_label, 3, 1, 1, 2)

        self.root_layout.addWidget(self.group)
        self.root_layout.addStretch(1)

        self.enabled_toggle.toggled.connect(self._on_enabled_change)
        self.tone_box.currentIndexChanged.connect(self._on_tone_change)
        self.volume_slider.valueChanged.connect(self._on_volume_preview)
        self.volume_slider.sliderReleased.connect(self._on_volume_change)
        self.prepare_button.clicked.connect(self._on_prepare)

    @asyncSlot(bool)
    async def _on_enabled_change(self, value: bool):
        async with qt_error_handler("OfbQtCaseSoundModule_SetEnabled", self.ctx):
            self.enabled_toggle.setEnabled(False)
            await self.ofb.set_property("case_sound", "enabled", json.dumps(value))

    @asyncSlot(int)
    async def _on_tone_change(self, index: int):
        if index < 0 or index >= len(self.tone_values):
            return
        async with qt_error_handler("OfbQtCaseSoundModule_SetTone", self.ctx):
            self.tone_box.setEnabled(False)
            await self.ofb.set_property("case_sound", "tone_id", self.tone_values[index])

    def _on_volume_preview(self, value: int):
        self.volume_label.setText(str(value))

    @asyncSlot()
    async def _on_volume_change(self, *_args):
        async with qt_error_handler("OfbQtCaseSoundModule_SetVolume", self.ctx):
            self.volume_slider.setEnabled(False)
            await self.ofb.set_property("case_sound", "volume", str(self.volume_slider.value()))

    @asyncSlot()
    async def _on_prepare(self, *_args):
        async with qt_error_handler("OfbQtCaseSoundModule_Prepare", self.ctx):
            self.prepare_button.setEnabled(False)
            await self.ofb.set_property("case_sound", "prepare", "true")

    async def update_ui(self, event: OfbCoreEvent):
        if not event.is_changed("case_sound") and not event.kind_match(OfbEventKind.DEVICE_CHANGED):
            return

        state = await self.ofb.get_property("case_sound") or {}
        visible = state.get("available") == "true"
        self.group.setVisible(visible)
        if self.list_item is not None:
            self.list_item.setVisible(visible)
        if not visible:
            return

        busy = state.get("transfer_status") in ("downloading", "transferring")
        self._update_status(state)

        with blocked_signals(self.enabled_toggle):
            self.enabled_toggle.setChecked(state.get("enabled") == "true")
        self.enabled_toggle.setEnabled(not busy)

        with blocked_signals(self.volume_slider):
            volume = int(state.get("volume", "0"))
            self.volume_slider.setValue(volume)
            self.volume_label.setText(str(volume))
        self.volume_slider.setEnabled(not busy and state.get("enabled") == "true")

        tone_id = state.get("tone_id", "0")
        with blocked_signals(self.tone_box):
            index = self.tone_values.index(tone_id) if tone_id in self.tone_values else 0
            self.tone_box.setCurrentIndex(index)
        self.tone_box.setEnabled(not busy and state.get("enabled") == "true")
        self.prepare_button.setEnabled(not busy)

    def _update_status(self, state: dict):
        status = state.get("transfer_status", "idle")
        progress = state.get("transfer_progress", "0")
        labels = {
            "idle": self.tr("Idle"),
            "ready": self.tr("Ready"),
            "downloading": self.tr("Downloading"),
            "transferring": self.tr("Transferring") + f" {progress}%",
            "failed": self.tr("Failed"),
        }
        label = labels.get(status, status)
        if status == "failed" and state.get("transfer_error"):
            label = f"{label}: {state['transfer_error']}"
        self.status_label.setText(label)