import json

from PyQt6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QGroupBox, QVBoxLayout
from qasync import asyncSlot

from openfreebuds import OfbEventKind
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.app.widget import clear_layout, make_settings_row, populate_rows
from openfreebuds_qt.qt_i18n import (
    get_device_adaptive_audio_names,
    get_device_config_option_names,
    get_device_feature_switch_names,
    get_service_language_names,
)
from openfreebuds_qt.utils.qt_utils import blocked_signals, qt_error_handler
from openfreebuds_qt.designer.device_other import Ui_OfbQtDeviceOtherSettingsModule


class OfbQtDeviceOtherSettingsModule(Ui_OfbQtDeviceOtherSettingsModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lang_options: list[str] = []
        self.adaptive_audio_toggles: dict[str, QCheckBox] = {}
        self.feature_toggles: dict[str, QCheckBox] = {}
        self.feature_toggle_rows: dict[str, QGroupBox] = {}
        self.feature_toggle_handlers = []
        self.config_option_boxes: dict[str, QComboBox] = {}
        self.config_option_rows: dict[str, QGroupBox] = {}
        self.config_option_values: dict[str, list[str]] = {}
        self.config_option_handlers = []
        self.language_option_names = get_service_language_names()
        self.adaptive_audio_feature_names = get_device_adaptive_audio_names()
        self.feature_switch_names = get_device_feature_switch_names()
        self.config_option_names = get_device_config_option_names()

        self.setupUi(self)
        self._rebuild_static_sections()
        self._setup_adaptive_audio_switches()
        self._setup_feature_switches()
        self._setup_config_options()

    def _rebuild_static_sections(self):
        auto_pause_title = self.auto_pause_toggle.text()
        auto_pause_description = self.label.text()
        self.auto_pause_toggle.setText("")
        self._replace_group_layout(
            self.auto_pause_root.layout(),
            [make_settings_row(self.auto_pause_root, auto_pause_title, auto_pause_description, [self.auto_pause_toggle])],
            [self.auto_pause_toggle],
        )

        low_latency_title = self.low_latency_toggle.text()
        low_latency_description = self.label_3.text()
        self.low_latency_toggle.setText("")
        self._replace_group_layout(
            self.low_latency_root.layout(),
            [make_settings_row(self.low_latency_root, low_latency_title, low_latency_description, [self.low_latency_toggle])],
            [self.low_latency_toggle],
        )

        self._replace_group_layout(
            self.service_language_root.layout(),
            [make_settings_row(
                self.service_language_root,
                self.label_2.text().rstrip(":"),
                self.label_4.text(),
                [self.service_language_box],
            )],
            [self.service_language_box],
            2,
        )

    @staticmethod
    def _replace_group_layout(layout, rows, keep_widgets, grid_column_span: int = 1):
        clear_layout(layout, keep_widgets=keep_widgets)
        populate_rows(layout, rows, grid_column_span if isinstance(layout, QGridLayout) else 1)

    def _setup_adaptive_audio_switches(self):
        self.adaptive_audio_root = QGroupBox(self.tr("Adaptive audio"), self)
        self.adaptive_audio_layout = QVBoxLayout(self.adaptive_audio_root)
        self.adaptive_audio_layout.setContentsMargins(0, 0, 0, 0)
        self.adaptive_audio_layout.setSpacing(12)

        for prop, label in self.adaptive_audio_feature_names.items():
            toggle = QCheckBox("", self.adaptive_audio_root)
            toggle.setObjectName(f"feature_{prop}_toggle")
            row = make_settings_row(self.adaptive_audio_root, label, "", [toggle])
            self.adaptive_audio_layout.addWidget(row)
            self.adaptive_audio_toggles[prop] = toggle
            self.feature_toggle_rows[prop] = row

            handler = self._make_feature_toggle_handler(prop, toggle)
            self.feature_toggle_handlers.append(handler)
            toggle.toggled.connect(handler)

        self.verticalLayout.insertWidget(2, self.adaptive_audio_root)
        self.adaptive_audio_root.setVisible(False)

    def _setup_feature_switches(self):
        self.feature_switches_root = QGroupBox(self.tr("Smart features"), self)
        self.feature_switches_layout = QVBoxLayout(self.feature_switches_root)
        self.feature_switches_layout.setContentsMargins(0, 0, 0, 0)
        self.feature_switches_layout.setSpacing(12)

        for prop, label in self.feature_switch_names.items():
            toggle = QCheckBox("", self.feature_switches_root)
            toggle.setObjectName(f"feature_{prop}_toggle")
            row = make_settings_row(self.feature_switches_root, label, "", [toggle])
            self.feature_switches_layout.addWidget(row)
            self.feature_toggles[prop] = toggle
            self.feature_toggle_rows[prop] = row

            handler = self._make_feature_toggle_handler(prop, toggle)
            self.feature_toggle_handlers.append(handler)
            toggle.toggled.connect(handler)

        self.verticalLayout.insertWidget(3, self.feature_switches_root)
        self.feature_switches_root.setVisible(False)

    def _setup_config_options(self):
        self.config_options_root = QGroupBox(self.tr("Device options"), self)
        self.config_options_layout = QVBoxLayout(self.config_options_root)
        self.config_options_layout.setContentsMargins(0, 0, 0, 0)
        self.config_options_layout.setSpacing(12)

        for prop, (label, options) in self.config_option_names.items():
            box = QComboBox(self.config_options_root)
            values = list(options.keys())
            box.addItems([options[value] for value in values])
            row = make_settings_row(self.config_options_root, label, "", [box])

            self.config_options_layout.addWidget(row)
            self.config_option_boxes[prop] = box
            self.config_option_rows[prop] = row
            self.config_option_values[prop] = values

            handler = self._make_config_option_handler(prop, box)
            self.config_option_handlers.append(handler)
            box.currentIndexChanged.connect(handler)

        self.verticalLayout.insertWidget(4, self.config_options_root)
        self.config_options_root.setVisible(False)

    def _all_feature_toggles(self):
        return {
            **self.adaptive_audio_toggles,
            **self.feature_toggles,
        }

    def _sync_visibility(self, features: dict, config: dict, service: dict):
        auto_pause_visible = "auto_pause" in config
        low_latency_visible = "low_latency" in config
        service_language_visible = "language" in service or "language_options" in service

        self.auto_pause_root.setVisible(auto_pause_visible)
        self.low_latency_root.setVisible(low_latency_visible)
        self.service_language_root.setVisible(service_language_visible)

        adaptive_audio_visible = False
        for prop, toggle in self.adaptive_audio_toggles.items():
            visible = prop in features
            self.feature_toggle_rows[prop].setVisible(visible)
            adaptive_audio_visible = adaptive_audio_visible or visible
        self.adaptive_audio_root.setVisible(adaptive_audio_visible)

        feature_switch_visible = False
        for prop, toggle in self.feature_toggles.items():
            visible = prop in features
            self.feature_toggle_rows[prop].setVisible(visible)
            feature_switch_visible = feature_switch_visible or visible
        self.feature_switches_root.setVisible(feature_switch_visible)

        config_options_visible = False
        for prop, box in self.config_option_boxes.items():
            visible = prop in config
            self.config_option_rows[prop].setVisible(visible)
            config_options_visible = config_options_visible or visible
        self.config_options_root.setVisible(config_options_visible)

        self.list_item.setVisible(
            auto_pause_visible
            or service_language_visible
            or low_latency_visible
            or adaptive_audio_visible
            or feature_switch_visible
            or config_options_visible
        )

    async def _apply_property_change(self, action_name: str, group: str, prop: str, value: str):
        try:
            await self.try_set_property(group, prop, value, action_name)
            await self.update_ui(OfbCoreEvent(None))
        except Exception:
            async with qt_error_handler(action_name, self.ctx):
                raise

    def _make_feature_toggle_handler(self, prop: str, toggle: QCheckBox):
        @asyncSlot(bool)
        async def _handler(value: bool):
            toggle.setEnabled(False)
            await self._apply_property_change(
                "OfbQtDeviceOtherSettingsModule_SetFeatureSwitch",
                "features",
                prop,
                json.dumps(value),
            )

        return _handler

    def _make_config_option_handler(self, prop: str, box: QComboBox):
        @asyncSlot(int)
        async def _handler(index: int):
            if index < 0:
                return
            box.setEnabled(False)
            await self._apply_property_change(
                "OfbQtDeviceOtherSettingsModule_SetConfigOption",
                "config",
                prop,
                self.config_option_values[prop][index],
            )

        return _handler

    async def update_ui(self, event: OfbCoreEvent):
        async with qt_error_handler("OfbQtDeviceOtherSettingsModule_UpdateUi", self.ctx):
            if event.kind_match(OfbEventKind.DEVICE_CHANGED) or event.is_prop_group_in(["config", "features", "service"]):
                features = await self.ofb.get_property("features") or {}
                config = await self.ofb.get_property("config") or {}
                service = await self.ofb.get_property("service") or {}
                self._sync_visibility(features, config, service)

            if event.is_changed("config", "auto_pause"):
                with blocked_signals(self.auto_pause_toggle):
                    self.auto_pause_toggle.setChecked(await self.ofb.get_property("config", "auto_pause") == "true")

            if event.is_changed("config", "low_latency"):
                with blocked_signals(self.low_latency_toggle):
                    self.low_latency_toggle.setChecked(await self.ofb.get_property("config", "low_latency") == "true")
                    self.low_latency_toggle.setEnabled(True)

            for prop, toggle in self._all_feature_toggles().items():
                if event.is_changed("features", prop):
                    with blocked_signals(toggle):
                        toggle.setChecked(await self.ofb.get_property("features", prop) == "true")
                        toggle.setEnabled(True)

            for prop, box in self.config_option_boxes.items():
                if event.is_changed("config", prop):
                    value = await self.ofb.get_property("config", prop)
                    with blocked_signals(box):
                        index = self.config_option_values[prop].index(value) if value in self.config_option_values[prop] else -1
                        box.setCurrentIndex(index)
                        box.setEnabled(True)

            if event.is_changed("service", "language_options"):
                options = await self.ofb.get_property("service", "language_options")
                if options is not None:
                    self.lang_options = options.split(",")
                    with blocked_signals(self.service_language_box):
                        self.service_language_box.clear()
                        self.service_language_box.addItems(
                            [self.language_option_names.get(o, o) for o in self.lang_options]
                        )
                        self.service_language_box.setCurrentIndex(-1)

    @asyncSlot(bool)
    async def on_low_latency_toggle(self, value: bool):
        self.low_latency_toggle.setEnabled(False)
        await self._apply_property_change(
            "OfbQtDeviceOtherSettingsModule_SetLowLatency",
            "config",
            "low_latency",
            json.dumps(value),
        )

    @asyncSlot(bool)
    async def on_auto_pause_toggle(self, value: bool):
        await self._apply_property_change(
            "OfbQtDeviceOtherSettingsModule_SetAutoPause",
            "config",
            "auto_pause",
            json.dumps(value),
        )

    @asyncSlot(int)
    async def on_language_select(self, index: int):
        await self._apply_property_change(
            "OfbQtDeviceOtherSettingsModule_SetLanguage",
            "service",
            "language",
            self.lang_options[index],
        )
