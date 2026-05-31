from dataclasses import dataclass
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QLabel, QVBoxLayout
from qasync import asyncSlot

from openfreebuds import OfbEventKind
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.utils.qt_utils import fill_combo_box
from openfreebuds_qt.designer.module_geatures import Ui_OfbQtGesturesModule

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
            r, c, rs, _ = self.grid.getItemPosition(index)
            self.grid.takeAt(index)
            self.grid.addWidget(self.left_combo, r, c, rs, 1 if value else 2)
            self.right_combo.setVisible(value)
        self._right_available = value


class OfbQtGesturesModule(Ui_OfbQtGesturesModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.gesture_names = {
            "tap_action_answer": self.tr("Answer to call"),
            "tap_action_change_volume": self.tr("Adjust volume"),
            "tap_action_assistant": self.tr("Voice assistant"),
            "tap_action_next": self.tr("Next track"),
            "tap_action_off": self.tr("Disabled"),
            "tap_action_pause": self.tr("Play/pause"),
            "tap_action_prev": self.tr("Prev track"),
            "tap_action_short_audio": self.tr("Short audio"),
            "tap_action_end_call": self.tr("End/reject call"),
            "tap_action_switch_device": self.tr("Switch device"),
            "tap_action_switch_anc": self.tr("Switch noise control mode"),
        }

        self.anc_pref_names = {
            "noise_control_disabled": self.tr("Disabled"),
            "noise_control_off_on": self.tr("Off and cancellation"),
            "noise_control_off_on_aw": self.tr("Cycle all modes"),
            "noise_control_on_aw": self.tr("Cancellation and awareness"),
            "noise_control_off_aw": self.tr("Off and awareness"),
        }

        self._ui_rows: list[_UiRow] = []

        self.setupUi(self)
        self.label.setProperty("pageLead", True)
        self.label_2.setProperty("settingsMiniHeader", True)
        self.label_3.setProperty("settingsMiniHeader", True)
        self.light_long_label = QLabel(self.tr("Pinch and hold"), self)
        self.light_long_left = QComboBox(self)
        self.light_long_left.setObjectName("light_long_left")
        self.light_long_right = QComboBox(self)
        self.light_long_right.setObjectName("light_long_right")
        self.gridLayout.addWidget(self.light_long_label, 6, 0, 1, 1)
        self.gridLayout.addWidget(self.light_long_left, 6, 1, 1, 1)
        self.gridLayout.addWidget(self.light_long_right, 6, 2, 1, 1)
        self._add_shared_gesture_row("light_tap_call_once", self.tr("Pinch once in call"), 12)
        self._add_shared_gesture_row("light_tap_call_twice", self.tr("Pinch twice in call"), 13)
        self._add_shared_gesture_row("light_tap_once", self.tr("Pinch once"), 14)
        self._add_shared_gesture_row("light_tap_twice", self.tr("Pinch twice"), 15)
        self._add_shared_gesture_row("light_tap_three", self.tr("Pinch three times"), 16)

        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="double_tap",
                                     ui_names_map=self.gesture_names,
                                     label=self.double_label,
                                     left_combo=self.double_left,
                                     right_combo=self.double_right))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="double_tap_in_call",
                                     ui_names_map=self.gesture_names,
                                     label=self.double_in_call_label,
                                     left_combo=self.double_in_call_left,
                                     is_separate=False))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="triple_tap",
                                     ui_names_map=self.gesture_names,
                                     label=self.triple_label,
                                     left_combo=self.triple_left,
                                     right_combo=self.triple_right))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="long_tap_in_call",
                                     ui_names_map=self.gesture_names,
                                     label=self.long_in_call_label,
                                     left_combo=self.long_in_call,
                                     is_separate=False))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="long_tap",
                                     ui_names_map=self.gesture_names,
                                     label=self.long_label,
                                     left_combo=self.long_left,
                                     right_combo=self.long_right))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                         settings_prefix="light_long_tap",
                         ui_names_map=self.gesture_names,
                         label=self.light_long_label,
                         left_combo=self.light_long_left,
                         right_combo=self.light_long_right))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="noise_control",
                                     ui_names_map=self.anc_pref_names,
                                     label=self.long_anc_label,
                                     left_combo=self.long_anc_left))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="power_button",
                                     ui_names_map=self.gesture_names,
                                     label=self.power_label,
                                     left_combo=self.power_left,
                                     is_separate=False))
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix="swipe_gesture",
                                     ui_names_map=self.gesture_names,
                                     label=self.swipe_label,
                                     left_combo=self.swipe_left,
                                     is_separate=False))
        self._rebuild_sections_layout()

    def _rebuild_sections_layout(self):
        rows_by_prefix = {row.settings_prefix: row for row in self._ui_rows}
        self._sections: list[tuple[QGroupBox, list[_UiRow]]] = []

        while self.gridLayout.count():
            self.gridLayout.takeAt(0)

        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setVerticalSpacing(14)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout.addWidget(
            self._build_stereo_section(
                self.tr("Touch controls"),
                [
                    rows_by_prefix["double_tap"],
                    rows_by_prefix["triple_tap"],
                    rows_by_prefix["long_tap"],
                ],
                use_existing_headers=True,
            ),
            1,
            0,
        )
        self.gridLayout.addWidget(
            self._build_stereo_section(
                self.tr("Pinch gestures"),
                [
                    rows_by_prefix["light_long_tap"],
                    rows_by_prefix["light_tap_once"],
                    rows_by_prefix["light_tap_twice"],
                    rows_by_prefix["light_tap_three"],
                    rows_by_prefix["noise_control"],
                ],
            ),
            2,
            0,
        )
        self.gridLayout.addWidget(
            self._build_shared_section(
                self.tr("Call controls"),
                [
                    rows_by_prefix["double_tap_in_call"],
                    rows_by_prefix["long_tap_in_call"],
                    rows_by_prefix["light_tap_call_once"],
                    rows_by_prefix["light_tap_call_twice"],
                ],
            ),
            3,
            0,
        )
        self.gridLayout.addWidget(
            self._build_shared_section(
                self.tr("Device shortcuts"),
                [
                    rows_by_prefix["power_button"],
                    rows_by_prefix["swipe_gesture"],
                ],
            ),
            4,
            0,
        )
        self.gridLayout.setRowStretch(5, 1)

    def _build_stereo_section(self, title: str, rows: list[_UiRow], use_existing_headers: bool = False) -> QGroupBox:
        group = QGroupBox(title, self)
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(18, 18, 18, 18)
        group_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        if use_existing_headers:
            left_header = self.label_2
            right_header = self.label_3
        else:
            left_header = QLabel(self.tr("Left"), group)
            right_header = QLabel(self.tr("Right"), group)

        for header in (left_header, right_header):
            header.setProperty("settingsMiniHeader", True)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid.addWidget(left_header, 0, 1)
        grid.addWidget(right_header, 0, 2)

        for row_index, row in enumerate(rows, start=1):
            row.grid = grid
            grid.addWidget(row.label, row_index, 0)
            if row.right_combo is not None:
                grid.addWidget(row.left_combo, row_index, 1)
                grid.addWidget(row.right_combo, row_index, 2)
            else:
                grid.addWidget(row.left_combo, row_index, 1, 1, 2)

        group_layout.addLayout(grid)
        self._sections.append((group, list(rows)))
        return group

    def _build_shared_section(self, title: str, rows: list[_UiRow]) -> QGroupBox:
        group = QGroupBox(title, self)
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(18, 18, 18, 18)
        group_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1)

        for row_index, row in enumerate(rows):
            row.grid = grid
            grid.addWidget(row.label, row_index, 0)
            grid.addWidget(row.left_combo, row_index, 1)

        group_layout.addLayout(grid)
        self._sections.append((group, list(rows)))
        return group

    def _add_shared_gesture_row(self, settings_prefix: str, label_text: str, row_index: int):
        label = QLabel(label_text, self)
        combo = QComboBox(self)
        combo.setObjectName(settings_prefix)
        self.gridLayout.addWidget(label, row_index, 0, 1, 1)
        self.gridLayout.addWidget(combo, row_index, 1, 1, 2)
        self.setup_gesture_ui(_UiRow(grid=self.gridLayout,
                                     settings_prefix=settings_prefix,
                                     ui_names_map=self.gesture_names,
                                     label=label,
                                     left_combo=combo,
                                     is_separate=False))

    async def update_ui(self, event: OfbCoreEvent):
        if not event.is_changed("action") and not event.kind_match(OfbEventKind.DEVICE_CHANGED):
            return

        actions = await self.ofb.get_property("action")
        if not actions:
            return

        for row in self._ui_rows:
            options_id = f"{row.settings_prefix}_options"
            current_id = f"{row.settings_prefix}_left" if row.is_separate else row.settings_prefix
            right_id = f"{row.settings_prefix}_right"
            if current_id not in actions or options_id not in actions:
                row.set_visible(False)
                continue

            row.options = list(actions[f"{row.settings_prefix}_options"].split(","))
            right_available = right_id in actions and row.right_combo is not None

            row.set_visible(True)
            row.set_right_available(right_available)

            fill_combo_box(row.left_combo, row.options, row.ui_names_map, actions[current_id])
            if right_available:
                fill_combo_box(row.right_combo, row.options, row.ui_names_map, actions[right_id])

        for group, rows in getattr(self, "_sections", []):
            group.setVisible(any(row._visible for row in rows))

    def setup_gesture_ui(self, row: _UiRow):
        @asyncSlot(int)
        async def _on_change_left(index: int):
            ident = f"{row.settings_prefix}_left" if row.is_separate else row.settings_prefix
            value = row.options[index]
            await self.ofb.set_property("action", ident, value)

        @asyncSlot(int)
        async def _on_change_right(index: int):
            ident = f"{row.settings_prefix}_right"
            value = row.options[index]
            await self.ofb.set_property("action", ident, value)

        row.left_combo.currentIndexChanged[int].connect(_on_change_left)
        if row.right_combo is not None:
            row.right_combo.currentIndexChanged[int].connect(_on_change_right)

        self._ui_rows.append(row)
