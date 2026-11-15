import json

from PyQt6.QtCore import QTimer
from qasync import asyncSlot

from openfreebuds import OfbEventKind
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.utils.qt_utils import blocked_signals, fill_combo_box, qt_error_handler
from openfreebuds_qt.designer.device_other import Ui_OfbQtDeviceOtherSettingsModule

LANGUAGE_OPTION_MAPPING = {
    "en-GB": "English (British)",
    "zh-CN": "Chinese"
}

SPATIAL_MODES = ["head_tracking", "fixed"]
SPATIAL_ROOMS = ["default", "theater", "cinema", "concert_hall"]
HEAD_ACTIONS = ["none", "answer", "reject"]
ADAPTIVE_VOLUME_LEVELS = ["low", "default", "high"]

BOX_TONE_VOLUME_DEBOUNCE_MS = 300


class OfbQtDeviceOtherSettingsModule(Ui_OfbQtDeviceOtherSettingsModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lang_options: list[str] = []

        self.spatial_mode_names = {
            "head_tracking": self.tr("Head tracking"),
            "fixed": self.tr("Fixed"),
        }
        self.spatial_room_names = {
            "default": self.tr("Default"),
            "theater": self.tr("Theater"),
            "cinema": self.tr("Cinema"),
            "concert_hall": self.tr("Concert hall"),
        }
        self.head_action_names = {
            "none": self.tr("No action"),
            "answer": self.tr("Answer call"),
            "reject": self.tr("Reject call"),
        }
        self.adaptive_volume_level_names = {
            "low": self.tr("Low"),
            "default": self.tr("Default"),
            "high": self.tr("High"),
        }

        self.setupUi(self)

        self.box_tone_volume_timer = QTimer(self)
        self.box_tone_volume_timer.setSingleShot(True)
        self.box_tone_volume_timer.setInterval(BOX_TONE_VOLUME_DEBOUNCE_MS)
        self.box_tone_volume_timer.timeout.connect(self.on_box_tone_lid_volume_commit)

        self.spatial_audio_toggle.toggled.connect(self.on_spatial_audio_toggle)
        self.spatial_audio_mode_box.currentIndexChanged.connect(self.on_spatial_mode_select)
        self.spatial_audio_room_box.currentIndexChanged.connect(self.on_spatial_room_select)
        self.adaptive_volume_toggle.toggled.connect(self.on_adaptive_volume_toggle)
        self.adaptive_volume_level_box.currentIndexChanged.connect(self.on_adaptive_volume_level_select)
        self.head_control_toggle.toggled.connect(self.on_head_control_toggle)
        self.head_nod_box.currentIndexChanged.connect(self.on_head_nod_select)
        self.head_shake_box.currentIndexChanged.connect(self.on_head_shake_select)
        self.box_tone_toggle.toggled.connect(self.on_box_tone_toggle)
        self.box_tone_lid_toggle.toggled.connect(self.on_box_tone_lid_toggle)
        self.box_tone_lid_volume_slider.valueChanged.connect(self.on_box_tone_lid_volume_changed)

    async def update_ui(self, event: OfbCoreEvent):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_UpdateUi", self.ctx):
            if event.kind_match(OfbEventKind.DEVICE_CHANGED):
                # Visibility setup
                auto_pause_visible = await self.ofb.get_property("config", "auto_pause") is not None
                low_latency_visible = await self.ofb.get_property("config", "low_latency") is not None
                service_language_visible = await self.ofb.get_property("service", "language") is not None
                spatial_audio_visible = await self.ofb.get_property(
                    "sound", "spatial_audio_supported") == "true"
                adaptive_volume_visible = await self.ofb.get_property(
                    "sound", "adaptive_volume_supported") == "true"
                head_control_visible = await self.ofb.get_property(
                    "config", "head_control_supported") == "true"
                box_tone_visible = (
                    await self.ofb.get_property("config", "box_tone_supported") == "true"
                    or await self.ofb.get_property("config", "box_tone_lid_supported") == "true"
                )

                self.auto_pause_root.setVisible(auto_pause_visible)
                self.low_latency_root.setVisible(low_latency_visible)
                self.service_language_root.setVisible(service_language_visible)
                self.spatial_audio_root.setVisible(spatial_audio_visible)
                self.adaptive_volume_root.setVisible(adaptive_volume_visible)
                self.head_control_root.setVisible(head_control_visible)
                self.box_tone_root.setVisible(box_tone_visible)

                self.list_item.setVisible(
                    auto_pause_visible or service_language_visible or low_latency_visible
                    or spatial_audio_visible or adaptive_volume_visible
                    or head_control_visible or box_tone_visible
                )

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

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("sound", "spatial_audio"):
                spatial_enabled = await self.ofb.get_property("sound", "spatial_audio") == "true"
                with blocked_signals(self.spatial_audio_toggle):
                    self.spatial_audio_toggle.setChecked(spatial_enabled)
                self.spatial_audio_options.setEnabled(spatial_enabled)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("sound", "spatial_audio_mode"):
                current = await self.ofb.get_property("sound", "spatial_audio_mode")
                fill_combo_box(self.spatial_audio_mode_box, SPATIAL_MODES, self.spatial_mode_names, current)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("sound", "spatial_audio_room"):
                current = await self.ofb.get_property("sound", "spatial_audio_room")
                fill_combo_box(self.spatial_audio_room_box, SPATIAL_ROOMS, self.spatial_room_names, current)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("sound", "adaptive_volume"):
                adaptive_enabled = await self.ofb.get_property("sound", "adaptive_volume") == "true"
                with blocked_signals(self.adaptive_volume_toggle):
                    self.adaptive_volume_toggle.setChecked(adaptive_enabled)
                self.adaptive_volume_level_options.setEnabled(adaptive_enabled)

            if (event.kind_match(OfbEventKind.DEVICE_CHANGED)
                    or event.is_changed("sound", "adaptive_volume_level")
                    or event.is_changed("sound", "adaptive_volume_level_options")):
                level_options = await self.ofb.get_property("sound", "adaptive_volume_level_options")
                self.adaptive_volume_level_options.setVisible(level_options is not None)
                if level_options is not None:
                    current = await self.ofb.get_property("sound", "adaptive_volume_level")
                    fill_combo_box(self.adaptive_volume_level_box, level_options.split(","),
                                   self.adaptive_volume_level_names, current)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("config", "head_control_enabled"):
                head_enabled = await self.ofb.get_property("config", "head_control_enabled") == "true"
                with blocked_signals(self.head_control_toggle):
                    self.head_control_toggle.setChecked(head_enabled)
                self.head_control_options.setEnabled(head_enabled)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("config", "head_control_nod_action"):
                current = await self.ofb.get_property("config", "head_control_nod_action")
                fill_combo_box(self.head_nod_box, HEAD_ACTIONS, self.head_action_names, current)

            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_changed("config", "head_control_shake_action"):
                current = await self.ofb.get_property("config", "head_control_shake_action")
                fill_combo_box(self.head_shake_box, HEAD_ACTIONS, self.head_action_names, current)

            if (event.kind_match(OfbEventKind.DEVICE_CHANGED)
                    or event.is_changed("config", "box_tone_enabled")
                    or event.is_changed("config", "box_tone_lid_enabled")
                    or event.is_changed("config", "box_tone_lid_supported")
                    or event.is_changed("config", "box_tone_lid_volume")
                    or event.is_changed("state", "headset_in_box")):
                with blocked_signals(self.box_tone_toggle):
                    self.box_tone_toggle.setChecked(
                        await self.ofb.get_property("config", "box_tone_enabled") == "true")

                lid_supported = await self.ofb.get_property("config", "box_tone_lid_supported") == "true"
                headset_in_box = await self.ofb.get_property("state", "headset_in_box") == "true"

                with blocked_signals(self.box_tone_lid_toggle):
                    self.box_tone_lid_toggle.setChecked(
                        await self.ofb.get_property("config", "box_tone_lid_enabled") == "true")

                volume = await self.ofb.get_property("config", "box_tone_lid_volume")
                with blocked_signals(self.box_tone_lid_volume_slider):
                    if volume is not None:
                        try:
                            self.box_tone_lid_volume_slider.setValue(int(volume))
                        except ValueError:
                            pass
                    self.box_tone_lid_volume_value.setText(str(self.box_tone_lid_volume_slider.value()))

                self.box_tone_lid_options.setVisible(lid_supported)
                self.box_tone_toggle.setEnabled(headset_in_box)
                self.box_tone_lid_toggle.setEnabled(headset_in_box)
                self.box_tone_lid_volume_slider.setEnabled(headset_in_box)
                self.box_tone_lid_hint.setVisible(not headset_in_box)

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

    @asyncSlot(bool)
    async def on_spatial_audio_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetSpatialAudio", self.ctx):
            self.spatial_audio_options.setEnabled(value)
            await self.ofb.set_property("sound", "spatial_audio", json.dumps(value))

    @asyncSlot(int)
    async def on_spatial_mode_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetSpatialMode", self.ctx):
            value = self.spatial_audio_mode_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("sound", "spatial_audio_mode", value)

    @asyncSlot(int)
    async def on_spatial_room_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetSpatialRoom", self.ctx):
            value = self.spatial_audio_room_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("sound", "spatial_audio_room", value)

    @asyncSlot(bool)
    async def on_adaptive_volume_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetAdaptiveVolume", self.ctx):
            await self.ofb.set_property("sound", "adaptive_volume", json.dumps(value))

    @asyncSlot(int)
    async def on_adaptive_volume_level_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetAdaptiveVolumeLevel", self.ctx):
            value = self.adaptive_volume_level_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("sound", "adaptive_volume_level", value)

    @asyncSlot(bool)
    async def on_head_control_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetHeadControl", self.ctx):
            self.head_control_options.setEnabled(value)
            await self.ofb.set_property("config", "head_control_enabled", json.dumps(value))

    @asyncSlot(int)
    async def on_head_nod_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetHeadNod", self.ctx):
            value = self.head_nod_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("config", "head_control_nod_action", value)

    @asyncSlot(int)
    async def on_head_shake_select(self, index: int):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetHeadShake", self.ctx):
            value = self.head_shake_box.itemData(index)
            if value is not None:
                await self.ofb.set_property("config", "head_control_shake_action", value)

    @asyncSlot(bool)
    async def on_box_tone_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetBoxTone", self.ctx):
            await self.ofb.set_property("config", "box_tone_enabled", json.dumps(value))

    @asyncSlot(bool)
    async def on_box_tone_lid_toggle(self, value: bool):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetBoxToneLid", self.ctx):
            await self.ofb.set_property("config", "box_tone_lid_enabled", json.dumps(value))

    def on_box_tone_lid_volume_changed(self, value: int):
        self.box_tone_lid_volume_value.setText(str(value))
        self.box_tone_volume_timer.start()

    @asyncSlot()
    async def on_box_tone_lid_volume_commit(self):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_SetBoxToneVolume", self.ctx):
            volume = self.box_tone_lid_volume_slider.value()
            await self.ofb.set_property("config", "box_tone_lid_volume", str(volume))
