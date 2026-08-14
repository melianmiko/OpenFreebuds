import json

from PyQt6.QtWidgets import QGridLayout, QGroupBox, QLabel, QPushButton, QVBoxLayout, QWidget
from qasync import asyncSlot

from openfreebuds import OfbEventKind
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.utils.qt_utils import qt_error_handler


class OfbQtFindDeviceModule(OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setObjectName("OfbQtFindDeviceModule")
        self.root_layout = QVBoxLayout(self)

        self.group = QGroupBox(self.tr("Find earbuds"), self)
        self.grid = QGridLayout(self.group)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        self.grid.setColumnStretch(2, 1)

        self.grid.addWidget(QLabel(self.tr("Earbud"), self.group), 0, 0)
        self.grid.addWidget(QLabel(self.tr("Status"), self.group), 0, 1)
        self.grid.addWidget(QLabel(self.tr("Action"), self.group), 0, 2)

        self.status_labels: dict[str, QLabel] = {}
        self.start_buttons: dict[str, QPushButton] = {}
        self.stop_buttons: dict[str, QPushButton] = {}

        self._add_side_row("left", self.tr("Left"), 1)
        self._add_side_row("right", self.tr("Right"), 2)

        self.root_layout.addWidget(self.group)
        self.root_layout.addStretch(1)

    def _add_side_row(self, side: str, label: str, row: int):
        self.grid.addWidget(QLabel(label, self.group), row, 0)

        status = QLabel(self.tr("Idle"), self.group)
        self.status_labels[side] = status
        self.grid.addWidget(status, row, 1)

        start_button = QPushButton(self.tr("Play sound"), self.group)
        stop_button = QPushButton(self.tr("Stop"), self.group)
        self.start_buttons[side] = start_button
        self.stop_buttons[side] = stop_button

        buttons = QVBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.addWidget(start_button)
        buttons.addWidget(stop_button)
        button_box = QWidget(self.group)
        button_box.setLayout(buttons)
        self.grid.addWidget(button_box, row, 2)

        start_button.clicked.connect(self._make_signal_handler(side, True))
        stop_button.clicked.connect(self._make_signal_handler(side, False))

    def _make_signal_handler(self, side: str, value: bool):
        @asyncSlot()
        async def _handler(*_args):
            try:
                self.start_buttons[side].setEnabled(False)
                self.stop_buttons[side].setEnabled(False)
                await self.try_set_property(
                    "find_device",
                    side,
                    json.dumps(value),
                    "OfbQtFindDeviceModule_SetSound",
                )
                await self.update_ui(OfbCoreEvent(None))
            except Exception:
                async with qt_error_handler("OfbQtFindDeviceModule_SetSound", self.ctx):
                    raise

        return _handler

    async def update_ui(self, event: OfbCoreEvent):
        if not event.is_changed("find_device") and not event.kind_match(OfbEventKind.DEVICE_CHANGED):
            return

        state = await self.ofb.get_property("find_device") or {}
        visible = bool(state)
        self.group.setVisible(visible)
        if self.list_item is not None:
            self.list_item.setVisible(visible)

        for side in ("left", "right"):
            if side not in state:
                self.status_labels[side].setVisible(False)
                self.start_buttons[side].parentWidget().setVisible(False)
                continue

            playing = state[side] == "true"
            self.status_labels[side].setVisible(True)
            self.start_buttons[side].parentWidget().setVisible(True)
            self.status_labels[side].setText(self.tr("Playing") if playing else self.tr("Idle"))
            self.start_buttons[side].setEnabled(not playing)
            self.stop_buttons[side].setEnabled(playing)