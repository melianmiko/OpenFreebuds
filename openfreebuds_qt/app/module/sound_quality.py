import asyncio
import json

from PIL import Image, ImageQt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QSlider, QMenu, QInputDialog, QMessageBox, QFileDialog
from qasync import asyncSlot

from openfreebuds.exceptions import OfbTooManyItemsError
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.constants import ASSETS_PATH
from openfreebuds_qt.designer.sound_quality import Ui_OfbQtSoundQualityModule
from openfreebuds_qt.qt_i18n import get_eq_preset_names
from openfreebuds_qt.utils import get_qt_icon_colored
from openfreebuds_qt.utils.async_dialog import run_dialog_async
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.utils.qt_utils import fill_combo_box, blocked_signals, qt_error_handler

log = create_logger("OfbQtSoundQualityModule")


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

        self._eq_last_options: list[str] = []
        self._eq_rows: list[QSlider] = []
        self._last_preset_data: list[int] = []

        self.setupUi(self)

        self.undo_btn.setIcon(
            get_qt_icon_colored("undo", self.palette().text().color().getRgb())
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
        self.custom_eq.setVisible(False)

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

    async def update_ui(self, event: OfbCoreEvent):
        sound = await self.ofb.get_property("sound")
        self.list_item.setVisible(sound is not None)
        if sound is None:
            return

        self.custom_edit_button.setVisible("equalizer_rows" in sound)
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

        if event.is_changed("sound", "equalizer_preset"):
            value = sound.get("equalizer_preset")
            options = sound.get("equalizer_preset_options")
            self.eq_root.setVisible(value is not None and options is not None)
            if options is not None:
                self._eq_last_options = list(options.split(","))
                fill_combo_box(self.eq_preset_box, self._eq_last_options, self.eq_preset_option_names, value)

        if event.is_changed("sound", "equalizer_rows"):
            rows = json.loads(sound.get("equalizer_rows") or "null")
            self.custom_eq.setVisible(rows is not None)
            if rows is not None:
                self._last_preset_data = rows
                for i, value in enumerate(rows):
                    with blocked_signals(self._eq_rows[i]):
                        self._eq_rows[i].setValue(value)
                        self._eq_rows[i].setToolTip(str(value))

    @asyncSlot()
    async def on_custom_save(self):
        async with qt_error_handler("OfbQtSoundQualityModule_EqCustomSave", self.ctx):
            await self.ofb.set_property("sound", "equalizer_saved", "true")

    @asyncSlot()
    async def on_custom_reset(self):
        async with qt_error_handler("OfbQtSoundQualityModule_EqCustomReset", self.ctx):
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
            value = self._eq_last_options[index]
            await self.ofb.set_property("sound", "equalizer_preset", value)

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
                await self.ofb.set_property("sound", "equalizer_preset", dialog.textValue())
                return True
            except OfbTooManyItemsError:
                dialog = QMessageBox(QMessageBox.Icon.Critical,
                                     self.tr("Failed"),
                                     self.tr("Can't create: too many custom preset created in device."),
                                     QMessageBox.StandardButton.Ok)
                dialog.setWindowModality(Qt.WindowModality.WindowModal)
                await run_dialog_async(dialog)
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
            await self.ofb.set_property("sound", "equalizer_rows", "null")

    @asyncSlot()
    async def export_file(self):
        if await self.ofb.get_property("sound", "equalizer_rows") is None:
            return

        async with qt_error_handler("OfbQtSoundQualityModule_ExportFile", self.ctx):
            dialog = QFileDialog(self, self.tr("Save equalizer preset to file..."))
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
            dialog = QFileDialog(self, self.tr("Load equalizer preset from file..."))
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
            await self.ofb.set_property("sound", "equalizer_rows", data)
            await asyncio.sleep(0.25)
            await self.ofb.set_property("sound", "equalizer_saved", "true")
