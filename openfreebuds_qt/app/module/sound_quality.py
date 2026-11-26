import asyncio
import json

from PyQt6.QtCore import Qt, QPoint, QRectF, QTimer
from PyQt6.QtGui import QIcon, QPainter, QFont
from PyQt6.QtWidgets import (
    QSlider, QMenu, QInputDialog, QMessageBox, QFileDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QStyle, QStyleOptionSlider,
)
from qasync import asyncSlot

from openfreebuds.exceptions import OfbTooManyItemsError
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.designer.sound_quality import Ui_OfbQtSoundQualityModule
from openfreebuds_qt.qt_i18n import get_eq_preset_names
from openfreebuds_qt.utils import get_img_colored
from openfreebuds_qt.utils.async_dialog import run_dialog_async
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.utils.qt_utils import fill_combo_box, blocked_signals, qt_error_handler

log = create_logger("OfbQtSoundQualityModule")

EQ_FREQUENCIES = ["60", "125", "250", "500", "1k", "2k", "4k", "8k", "12k", "16k"]


def _format_eq_value(value: int) -> str:
    """
    Convert internal slider value (-60..60) to displayed value (-6.0..6.0).
    """
    return f"{value / 10:.1f}"


class EqScaleWidget(QWidget):
    """Vertical scale shown left of the equalizer sliders, in 2.0 dB steps.
    Tick positions are calculated with QSlider's own geometry (groove height + handle center) so labels/short lines align pixel-perfectly with Qt's ticks and handle center.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._slider: QSlider | None = None

    def set_slider(self, slider: QSlider):
        self._slider = slider
        self.update()

    def _y_of(self, internal: int) -> float:
        slider = self._slider
        option = QStyleOptionSlider()
        slider.initStyleOption(option)
        style = slider.style()

        groove = style.subControlRect(QStyle.ComplexControl.CC_Slider, option,
                                      QStyle.SubControl.SC_SliderGroove, slider)
        handle = style.subControlRect(QStyle.ComplexControl.CC_Slider, option,
                                      QStyle.SubControl.SC_SliderHandle, slider)
        span = max(groove.height() - handle.height(), 1)
        pos = style.sliderPositionFromValue(slider.minimum(), slider.maximum(),
                                            internal, span)
        local_y = groove.top() + pos + handle.height() / 2
        return self.mapFromGlobal(slider.mapToGlobal(QPoint(0, int(local_y)))).y()

    def paintEvent(self, _event):
        if self._slider is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        metrics = self.fontMetrics()

        for internal in range(60, -61, -20):
            y = self._y_of(internal)
            font = QFont(self.font())
            font.setBold(internal == 0)
            painter.setFont(font)
            painter.drawText(
                QRectF(0, y - metrics.height() / 2, self.width() - 6, metrics.height()),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                _format_eq_value(internal),
            )
            painter.drawLine(self.width() - 4, int(y), self.width(), int(y))


class OfbQtSoundQualityModule(Ui_OfbQtSoundQualityModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.eq_preset_option_names = get_eq_preset_names()

        self.menu_actions = [
            (self.tr("New preset…"), self.new_preset),
            (self.tr("Delete…"), self.delete_preset),
            (None, None),
            (self.tr("Export to file…"), self.export_file),
            (self.tr("Load file…"), self.load_file),
        ]

        self.dialog_preset_copy = QMessageBox(QMessageBox.Icon.Information,
                             self.tr("Notice"),
                             self.tr("This preset isn't available in your device, it will be created as "
                                     "custom preset."),
                             QMessageBox.StandardButton.Ok)
        self.dialog_preset_copy.setWindowModality(Qt.WindowModality.WindowModal)

        self.dialog_too_many_presets = QMessageBox(QMessageBox.Icon.Critical,
                             self.tr("Failed"),
                             self.tr("Can't create: too many custom preset created in device."),
                             QMessageBox.StandardButton.Ok)
        self.dialog_too_many_presets.setWindowModality(Qt.WindowModality.WindowModal)

        self._eq_last_options: list[str] = []
        self._eq_rows: list[QSlider] = []
        self._eq_value_labels: list[QLabel] = []
        self._last_preset_data: list[int] = []
        self._last_copy_options: list[str] = []

        self.setupUi(self)

        self.undo_btn.setIcon(
            QIcon(get_img_colored("undo", self.palette().text().color().getRgb()))
        )

        self.custom_menu = QMenu()
        self.custom_edit_button.setMenu(self.custom_menu)
        for name, action in self.menu_actions:
            if name is None:
                self.custom_menu.addSeparator()
            else:
                # noinspection PyUnresolvedReferences
                self.custom_menu.addAction(name).triggered.connect(action)

        for i in range(10):
            self._add_slider(i)
        self._add_scale()
        self.custom_eq.setVisible(False)
        self._eq_write_lock = asyncio.Lock()
        self._eq_debounce = QTimer(self)
        self._eq_debounce.setSingleShot(True)
        self._eq_debounce.setInterval(250)
        self._eq_debounce.timeout.connect(self._flush_eq)

    def _add_scale(self):
        self._eq_scale = EqScaleWidget(self.custom_eq_rows)
        self._eq_scale.setFixedWidth(34)
        self.custom_eq_rows_layout.insertWidget(0, self._eq_scale)
        self._eq_scale.set_slider(self._eq_rows[0])

    def _add_slider(self, i):
        def _on_change(value: int):
            # Drag/click snaps to a 0.5 dB grid (internal unit 0.1 dB)
            snapped = int(round(value / 5.0)) * 5
            if snapped != value:
                with blocked_signals(self._eq_rows[i]):
                    self._eq_rows[i].setValue(snapped)
                value = snapped

            self._eq_value_labels[i].setText(_format_eq_value(value))
            self._eq_rows[i].setToolTip(_format_eq_value(value))
            if not self._last_preset_data or len(self._last_preset_data) <= i:
                return
            self._last_preset_data[i] = value
            # All sliders share one write lock; after debounce, send the latest full data once
            self._eq_debounce.start()

        slider = QSlider(Qt.Orientation.Vertical)
        slider.setRange(-60, 60)
        slider.setSingleStep(5)
        slider.setPageStep(10)
        slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        # Each step on the slider is 1.0 dB (internal unit 0.1 dB); numeric ticks on the left remain 2 dB apart
        slider.setTickInterval(10)
        slider.setToolTip("0.0")
        # noinspection PyUnresolvedReferences
        slider.valueChanged.connect(_on_change)

        value_label = QLabel("0.0")
        value_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        value_font = QFont(value_label.font())
        value_font.setBold(True)
        value_label.setFont(value_font)

        freq_label = QLabel(EQ_FREQUENCIES[i])
        freq_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # A vertical QSlider's sizeHint is only the handle width, so spacers on both sides are required to align
        # the value above, the slider, and the band label below on one vertical axis
        slider_row = QHBoxLayout()
        slider_row.setContentsMargins(0, 0, 0, 0)
        slider_row.setSpacing(0)
        slider_row.addStretch(1)
        slider_row.addWidget(slider)
        slider_row.addStretch(1)

        column = QVBoxLayout()
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(2)
        column.addWidget(value_label)
        column.addLayout(slider_row, 1)
        column.addWidget(freq_label)

        wrapper = QWidget()
        wrapper.setLayout(column)
        self.custom_eq_rows_layout.addWidget(wrapper, 1)

        self._eq_value_labels.append(value_label)
        self._eq_rows.append(slider)

    async def update_ui(self, event: OfbCoreEvent):
        sound = await self.ofb.get_property("sound")
        self.list_item.setVisible(sound is not None)
        if sound is None:
            return

        self.custom_edit_button.setVisible(int(sound.get("equalizer_max_custom_modes", "0")) > 0)
        self.save_panel.setVisible(not json.loads(sound.get("equalizer_saved", "true")))

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

        if event.is_changed("sound", "equalizer_preset") or event.is_changed("sound", "equalizer_preset_options"):
            value = sound.get("equalizer_preset")
            options = sound.get("equalizer_preset_options")
            copy_options = sound.get("equalizer_preset_create_options")
            self.eq_root.setVisible(value is not None and options is not None)
            if copy_options is not None:
                self._last_copy_options = list(copy_options.split(","))
            if options is not None:
                self._eq_last_options = list(options.split(","))
                fill_combo_box(self.eq_preset_box, self._eq_last_options, self.eq_preset_option_names, value)
            if value is not None:
                self.custom_eq.setTitle(
                    self.tr("Customize preset") + f": {self.eq_preset_option_names.get(value, value)}"
                )

        if event.is_changed("sound", "equalizer_rows"):
            rows = json.loads(sound.get("equalizer_rows") or "null")
            self.custom_eq.setVisible(rows is not None)
            if rows is not None:
                self._last_preset_data = rows
                for i, value in enumerate(rows):
                    with blocked_signals(self._eq_rows[i]):
                        self._eq_rows[i].setValue(value)
                        self._eq_rows[i].setToolTip(_format_eq_value(value))
                        self._eq_value_labels[i].setText(_format_eq_value(value))

    @asyncSlot()
    async def _flush_eq(self):
        """Single write path after debounce: all sliders share one lock and send only the latest full 10-band values."""
        if self._eq_write_lock.locked():
            # If the previous write has not returned, resend later so the last change is not lost
            self._eq_debounce.start()
            return
        async with self._eq_write_lock:
            data = list(self._last_preset_data)
            try:
                await self.ofb.set_property("sound", "equalizer_rows", json.dumps(data))
            except TimeoutError:
                # FreeClip 2 sometimes answers 0x2B49 with only 0x2B4A; the device did apply it, so do not throw the stack into qasync
                log.warning("EQ write timed out, local values kept")
            except Exception:
                log.exception("EQ write failed, local values kept")

    async def _flush_now(self):
        """Before saving/creating a preset, flush pending changes immediately."""
        if self._eq_debounce.isActive():
            self._eq_debounce.stop()
        await self._flush_eq()

    def _drop_pending(self):
        """Before reset/switching/deleting a preset, discard pending changes."""
        if self._eq_debounce.isActive():
            self._eq_debounce.stop()

    @asyncSlot()
    async def on_custom_save(self):
        async with qt_error_handler("OfbQtSoundQualityModule_EqCustomSave", self.ctx):
            await self._flush_now()
            await self.ofb.set_property("sound", "equalizer_saved", "true")

    @asyncSlot()
    async def on_custom_reset(self):
        async with qt_error_handler("OfbQtSoundQualityModule_EqCustomReset", self.ctx):
            self._drop_pending()
            await self.ofb.set_property("sound", "equalizer_saved", "false")

    @asyncSlot()
    async def on_sq_set_connectivity(self):
        async with qt_error_handler("OfbQtSoundQualityModule_SetConnectivity", self.ctx):
            await self.ofb.set_property("sound", "quality_preference", "sqp_connectivity")

    @asyncSlot()
    async def on_sq_set_quality(self):
        async with qt_error_handler("OfbQtSoundQualityModule_SetQuality", self.ctx):
            await self.ofb.set_property("sound", "quality_preference", "sqp_quality")

    @asyncSlot(int)
    async def on_eq_preset_change(self, index: int):
        async with qt_error_handler("OfbQtSoundQualityModule_ChangePreset", self.ctx):
            self._drop_pending()
            value = self._eq_last_options[index]

            if value in self._last_copy_options:
                self.dialog_preset_copy.show()

            try:
                await self.ofb.set_property("sound", "equalizer_preset", value)
            except OfbTooManyItemsError:
                self.dialog_too_many_presets.show()

    @asyncSlot()
    async def new_preset(self):
        async with qt_error_handler("OfbQtSoundQualityModule_NewPreset", self.ctx):
            try:
                dialog = QInputDialog(self)
                dialog.setWindowModality(Qt.WindowModality.WindowModal)
                dialog.setInputMode(QInputDialog.InputMode.TextInput)
                dialog.setWindowTitle(self.tr("Create new equalizer preset"))
                dialog.setLabelText(self.tr("Enter new preset name:"))
                if not await run_dialog_async(dialog):
                    return False

                log.info(f"Create new mode with name {dialog.textValue()}")
                await self._flush_now()
                await self.ofb.set_property("sound", "equalizer_preset", dialog.textValue())
                return True
            except OfbTooManyItemsError:
                self.dialog_too_many_presets.show()
                return False

    @asyncSlot()
    async def delete_preset(self):
        if await self.ofb.get_property("sound", "equalizer_rows") is None:
            return

        async with qt_error_handler("OfbQtSoundQualityModule_DeletePreset", self.ctx):
            dialog = QMessageBox(QMessageBox.Icon.Question,
                                 self.tr("Delete equalizer mode?"),
                                 self.tr("Will delete following mode:") + "\n" + self.eq_preset_box.currentText(),
                                 QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                                 self)
            dialog.setWindowModality(Qt.WindowModality.WindowModal)
            if not await run_dialog_async(dialog):
                return

            log.info(f"Delete mode with name {self.eq_preset_box.currentText()}")
            self._drop_pending()
            await self.ofb.set_property("sound", "equalizer_rows", "null")

    @asyncSlot()
    async def export_file(self):
        if await self.ofb.get_property("sound", "equalizer_rows") is None:
            return

        async with qt_error_handler("OfbQtSoundQualityModule_ExportFile", self.ctx):
            dialog = QFileDialog(self, self.tr("Save equalizer preset to file…"))
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, False)
            dialog.setWindowModality(Qt.WindowModality.WindowModal)
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            if not await run_dialog_async(dialog):
                return
            paths = dialog.selectedFiles()
            if len(paths) < 1:
                return

            with open(paths[0], "w") as f:
                f.write(await self.ofb.get_property("sound", "equalizer_rows"))

    @asyncSlot()
    async def load_file(self):
        async with qt_error_handler("OfbQtSoundQualityModule_LoadFile", self.ctx):
            dialog = QFileDialog(self, self.tr("Load equalizer preset from file…"))
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, False)
            dialog.setWindowModality(Qt.WindowModality.WindowModal)
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            if not await run_dialog_async(dialog):
                return
            paths = dialog.selectedFiles()
            if len(paths) < 1:
                return

            with open(paths[0], "r") as f:
                data = f.read()

            if not await self.new_preset():
                return
            await asyncio.sleep(0.5)
            self._drop_pending()
            await self.ofb.set_property("sound", "equalizer_rows", data)
            await asyncio.sleep(0.25)
            await self.ofb.set_property("sound", "equalizer_saved", "true")
