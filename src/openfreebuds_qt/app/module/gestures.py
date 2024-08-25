from dataclasses import dataclass
from typing import Optional

from PyQt6.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout
from qasync import asyncSlot

from openfreebuds import IOpenFreebuds
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.designer.module_geatures import Ui_OfbQtGesturesModule
from openfreebuds_qt.i18n_mappings import GESTURE_ACTION_MAPPINGS, NOISE_CONTROL_OPTION_MAPPING

log = create_logger("OfbQtGesturesModule")


@dataclass
class _UiRow:
    settings_prefix: str
    grid: QGridLayout
    ui_names_map: dict[str, str]
    label: QLabel
    left_combo: QComboBox
    options: Optional[list[str]] = None
    right_combo: Optional[QComboBox] = None
    is_separate: bool = True
    _right_available: bool = True
    _visible: bool = True

    def set_visible(self, value: bool):
        if value == self._visible:
            return
        self.label.setVisible(value)
        self.left_combo.setVisible(value)
        if self.right_combo is not None:
            self.right_combo.setVisible(value)
        self._visible = value

    def set_right_available(self, value: bool):
        if value == self._right_available or not self._visible:
            return
        if self.right_combo is not None:
            index = self.grid.indexOf(self.left_combo)
            r, c, rs, cs = self.grid.getItemPosition(index)
            self.grid.takeAt(index)
            self.grid.addWidget(self.left_combo, r, c, rs, 1 if value else 2)
            self.right_combo.setVisible(value)
        self._right_available = value


class OfbQtGesturesModule(Ui_OfbQtGesturesModule, OfbQtCommonModule):
    def __init__(self, parent: QWidget, ofb: IOpenFreebuds):
        super().__init__(parent)

        self._ui_rows: list[_UiRow] = []

        self.ofb: IOpenFreebuds = ofb

        self.setupUi(self)
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="double_tap",
                                     ui_names_map=GESTURE_ACTION_MAPPINGS,
                                     label=self.double_label,
                                     left_combo=self.double_left,
                                     right_combo=self.double_right))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="double_tap_in_call",
                                     ui_names_map=GESTURE_ACTION_MAPPINGS,
                                     label=self.double_in_call_label,
                                     left_combo=self.double_in_call_left,
                                     is_separate=False))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="triple_tap",
                                     ui_names_map=GESTURE_ACTION_MAPPINGS,
                                     label=self.triple_label,
                                     left_combo=self.triple_left,
                                     right_combo=self.triple_right))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="long_tap",
                                     ui_names_map=GESTURE_ACTION_MAPPINGS,
                                     label=self.long_label,
                                     left_combo=self.long_left,
                                     right_combo=self.long_right))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="noise_control",
                                     ui_names_map=NOISE_CONTROL_OPTION_MAPPING,
                                     label=self.long_anc_label,
                                     left_combo=self.long_anc_left))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="power_button",
                                     ui_names_map=GESTURE_ACTION_MAPPINGS,
                                     label=self.power_label,
                                     left_combo=self.power_left,
                                     is_separate=False))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="swipe_gesture",
                                     ui_names_map=GESTURE_ACTION_MAPPINGS,
                                     label=self.swipe_label,
                                     left_combo=self.swipe_left,
                                     is_separate=False))

    async def update_ui(self, event: OfbCoreEvent):
        if not event.is_changed("action"):
            return

        actions = await self.ofb.get_property("action")
        if not actions:
            return

        for row in self._ui_rows:
            options_id = f"{row.settings_prefix}_options"
            current_id = f"{row.settings_prefix}_left" if row.is_separate else row.settings_prefix
            right_id = f"{row.settings_prefix}_right"
            if current_id not in actions or options_id not in actions:
                log.info(f"Row {row.settings_prefix} unavailable")
                row.set_visible(False)
                continue

            row.options = list(actions[f"{row.settings_prefix}_options"].split(","))
            right_available = right_id in actions and row.right_combo is not None

            row.set_visible(True)
            row.set_right_available(right_available)

            self._fill_combo_box(row.left_combo, row.options, row.ui_names_map, actions[current_id])
            if right_available:
                self._fill_combo_box(row.right_combo, row.options, row.ui_names_map, actions[right_id])

    def _fill_combo_box(self, box: QComboBox, options: list[str], name_map: dict[str, str], current: str):
        box.blockSignals(True)
        box.clear()
        box.addItems([self.tr(name_map.get(i, i)) for i in options])
        for index, value in enumerate(options):
            box.setItemData(index, value)

        box.setCurrentIndex(options.index(current))
        box.blockSignals(False)

    def setup_gesture_ui(self, row: _UiRow):
        @asyncSlot(int)
        async def _on_change_left(index: int):
            ident = f"{row.settings_prefix}_left" if row.is_separate else row.settings_prefix
            value = row.options[index]
            log.info(f"SET {ident} -> {value}")
            await self.ofb.set_property("action", ident, value)

        @asyncSlot(int)
        async def _on_change_right(index: int):
            ident = f"{row.settings_prefix}_right"
            value = row.options[index]
            log.info(f"SET {ident} -> {value}")
            await self.ofb.set_property("action", ident, value)

        row.left_combo.currentIndexChanged[int].connect(_on_change_left)
        if row.right_combo is not None:
            row.right_combo.currentIndexChanged[int].connect(_on_change_right)

        self._ui_rows.append(row)
