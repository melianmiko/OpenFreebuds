from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QSpinBox, QFormLayout,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)
from qasync import asyncSlot

from openfreebuds import OfbEventKind
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.tray.battery import battery_style, percentage_icon
from openfreebuds_qt.utils import blocked_signals
from openfreebuds_qt.utils.async_dialog import run_dialog_async


class OfbQtTrayBatteryModule(OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = OfbQtConfigParser.get_instance()
        layout = QVBoxLayout(self)
        self.enabled = QCheckBox(self.tr("Show battery percentages in the system tray"))
        self.enabled.setChecked(self.config.get("ui", "tray_battery_percentages", False))
        layout.addWidget(self.enabled)
        form = QFormLayout()
        self.component = QComboBox()
        for label, key in ((self.tr("Left earbud"), "left"), (self.tr("Right earbud"), "right"),
                           (self.tr("Charging case"), "case")):
            self.component.addItem(label, key)
        form.addRow(self.tr("Customize indicator"), self.component)
        self.text_button = QPushButton()
        self.background_button = QPushButton()
        form.addRow(self.tr("Text color"), self.text_button)
        form.addRow(self.tr("Background color"), self.background_button)
        self.font_scale = QSpinBox()
        self.font_scale.setRange(50, 100)
        self.font_scale.setSuffix("%")
        self.font_scale.setSingleStep(5)
        form.addRow(self.tr("Text size (100% = largest that fits)"), self.font_scale)
        layout.addLayout(form)
        self.transparent = QCheckBox(self.tr("Transparent background"))
        layout.addWidget(self.transparent)
        layout.addWidget(QLabel(self.tr("Preview")))
        preview = QHBoxLayout()
        self.previews = []
        for label, key, level in ((self.tr("Left earbud"), "left", 50), (self.tr("Right earbud"), "right", 65),
                             (self.tr("Charging case"), "case", 85)):
            column = QVBoxLayout()
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            caption = QLabel(label)
            caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
            column.addWidget(icon)
            column.addWidget(caption)
            preview.addLayout(column)
            self.previews.append((icon, key, level))
        layout.addLayout(preview)
        hint = QLabel(self.tr("Changes apply immediately. Icons appear when battery levels are available. "
                             "On Windows, check the hidden icons (^) menu and drag the icons onto the taskbar."))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()
        self.enabled.toggled.connect(self.on_enabled)
        self.transparent.toggled.connect(self.on_transparent)
        self.text_button.clicked.connect(self.on_text_color)
        self.background_button.clicked.connect(self.on_background_color)
        self.component.currentIndexChanged.connect(self.refresh_preview)
        self.font_scale.valueChanged.connect(self.on_font_scale)
        self.refresh_preview()

    def setting_key(self, name):
        return f"tray_battery_{self.component.currentData()}_{name}"

    def color(self, key, fallback):
        value = self.config.get("ui", key, fallback)
        return value if isinstance(value, str) and QColor(value).isValid() else fallback

    def refresh_preview(self, *_):
        text, background, transparent, scale = battery_style(self.config, self.component.currentData())
        self.text_button.setText(text)
        self.background_button.setText(background)
        with blocked_signals(self.transparent):
            self.transparent.setChecked(bool(transparent))
        with blocked_signals(self.font_scale):
            self.font_scale.setValue(scale)
        self.background_button.setEnabled(not transparent)
        for icon, key, level in self.previews:
            text, background, transparent, scale = battery_style(self.config, key)
            icon.setPixmap(percentage_icon(
                level, "light", text, None if transparent else background, scale
            ).pixmap(32, 32))

    async def save(self, key, value):
        self.config.set("ui", key, value)
        self.config.save()
        self.refresh_preview()
        await self.ofb.send_message(OfbEventKind.QT_SETTINGS_CHANGED)

    @asyncSlot(bool)
    async def on_enabled(self, value):
        await self.save("tray_battery_percentages", value)

    @asyncSlot(bool)
    async def on_transparent(self, value):
        await self.save(self.setting_key("transparent"), value)

    @asyncSlot(int)
    async def on_font_scale(self, value):
        await self.save(self.setting_key("font_scale"), value)

    async def choose_color(self, key, fallback):
        dialog = QColorDialog(QColor(self.color(key, fallback)), self)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        try:
            if await run_dialog_async(dialog):
                color = dialog.selectedColor()
                if color.isValid():
                    await self.save(key, color.name())
        finally:
            dialog.hide()
            dialog.deleteLater()

    @asyncSlot()
    async def on_text_color(self):
        await self.choose_color(self.setting_key("text_color"), self.text_button.text())

    @asyncSlot()
    async def on_background_color(self):
        await self.choose_color(self.setting_key("background_color"), self.background_button.text())
