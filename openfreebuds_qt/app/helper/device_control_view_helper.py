import asyncio
from typing import Optional

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from qasync import asyncSlot

from openfreebuds import OfbEventKind, IOpenFreebuds
from openfreebuds.utils import reverse_dict
from openfreebuds_qt.designer.main_window import Ui_OfbMainWindowDesign
from openfreebuds_qt.generic import IOfbQtApplication
from openfreebuds_qt.qt_i18n import get_anc_level_names
from openfreebuds_qt.utils import OfbCoreEvent, blocked_signals, get_img_colored


class OfbQtDeviceControlViewHelper:
    def __init__(self, ctx: IOfbQtApplication, ui: Ui_OfbMainWindowDesign):
        self.ui = ui
        self.ctx = ctx
        self.ofb = ctx.ofb
        self._task: Optional[asyncio.Task] = None

        self.anc_level_option_names = get_anc_level_names()
        
        text_color = ctx.palette().text().color().getRgb()
        icon_batt_l = get_img_colored("batt_l", text_color, "icon/main_window", (16, 16))
        icon_batt_r = get_img_colored("batt_r", text_color, "icon/main_window", (16, 16))
        icon_batt_c = get_img_colored("batt_c", text_color, "icon/main_window", (16, 16))

        self.ui.anc_awr.setIcon(QIcon(get_img_colored("anc_awr", text_color, "icon/main_window")))
        self.ui.anc_off.setIcon(QIcon(get_img_colored("anc_off", text_color, "icon/main_window")))
        self.ui.anc_on.setIcon(QIcon(get_img_colored("anc_on", text_color, "icon/main_window")))

        self.ui.batt_l_icon.setPixmap(icon_batt_l)
        self.ui.batt_r_icon.setPixmap(icon_batt_r)
        self.ui.batt_c_icon.setPixmap(icon_batt_c)
        self.ui.anc_on.clicked.connect(self.set_anc_on)
        self.ui.anc_off.clicked.connect(self.set_anc_off)
        self.ui.anc_awr.clicked.connect(self.set_anc_awr)
        self.ui.anc_level.currentTextChanged.connect(self.set_anc_level)
        self.ui.control_root.setVisible(False)

    def set_anc_level(self, value):
        code = reverse_dict(self.anc_level_option_names).get(value)
        self._task = asyncio.create_task(
            self.ofb.set_property("anc", "level", code)
        )

    def set_anc_off(self):
        self._task = asyncio.create_task(
            self.ofb.set_property("anc", "mode", "normal")
        )

    def set_anc_on(self):
        self._task = asyncio.create_task(
            self.ofb.set_property("anc", "mode", "cancellation")
        )

    def set_anc_awr(self):
        self._task = asyncio.create_task(
            self.ofb.set_property("anc", "mode", "awareness")
        )

    async def update_ui(self, event: OfbCoreEvent):
        force_render = False

        if event.kind_match(OfbEventKind.STATE_CHANGED):
            state = await self.ofb.get_state()
            visible = state == IOpenFreebuds.STATE_CONNECTED
            self.ui.control_root.setVisible(visible)
            force_render = True

            title = "OpenFreebuds"
            if visible:
                title, _ = await self.ofb.get_device_tags()
            elif state == IOpenFreebuds.STATE_WAIT:
                title = QApplication.translate("OfbQtDeviceControlViewHelper", "Connecting…")
            self.ui.device_name_view.setText(title)

        if event.is_changed("battery", "") or force_render:
            battery = await self.ofb.get_property("battery")
            if battery is not None:
                await self._update_battery(battery)

        if event.is_changed("anc") or force_render:
            anc = await self.ofb.get_property("anc")
            self.ui.anc_root.setVisible(anc is not None)
            if anc is not None:
                await self._update_anc(anc)

    async def _update_anc(self, anc: dict):
        mode = anc["mode"]
        self.ui.anc_on.setChecked(mode == "cancellation")
        self.ui.anc_awr.setChecked(mode == "awareness")
        self.ui.anc_off.setChecked(mode == "normal")

        level = anc.get("level", None)
        self.ui.anc_level.setVisible(level is not None)
        if level is not None:
            options = anc["level_options"].split(",")
            with blocked_signals(self.ui.anc_level):
                self.ui.anc_level.clear()
                for opt_code in options:
                    self.ui.anc_level.addItem(self.anc_level_option_names.get(opt_code, opt_code))
                self.ui.anc_level.setCurrentText(self.anc_level_option_names.get(level, level))

    async def _update_battery(self, battery: dict):
        is_tws = "case" in battery
        self.ui.batt_l_root.setVisible(is_tws)
        self.ui.batt_r_root.setVisible(is_tws)
        self.ui.batt_l_text.setText(f'{battery.get("left", "--")}%')
        self.ui.batt_r_text.setText(f'{battery.get("right", "--")}%')
        self.ui.batt_c_text.setText(f'{battery.get("case" if is_tws else "global", "--")}%')
