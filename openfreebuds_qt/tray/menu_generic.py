from typing import Optional

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QWidget

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.utils.core_event import OfbCoreEvent


class OfbQtTrayMenuCommon(QMenu):
    def __init__(self, parent: QWidget, ofb: IOpenFreebuds):
        super().__init__(parent)
        self._sections: list[list[QAction]] = [[]]
        self._section_visible: list[bool] = [True]
        self.ofb: IOpenFreebuds = ofb

    async def on_core_event(self, event: OfbCoreEvent, state: int):
        pass

    def new_section(self):
        self._sections.append([])
        self._section_visible.append(True)
        return len(self._sections) - 1

    def set_section_visible(self, section: int, value: bool):
        if self._section_visible[section] == value:
            return

        for i in self._sections[section]:
            i.setVisible(value)
        self._section_visible[section] = value

    def add_separator(self):
        item = super().addSeparator()
        self._sections[-1].append(item)
        return item

    def add_menu(self, menu: QMenu):
        item = super().addMenu(menu)
        self._sections[-1].append(item)
        return item

    def add_item(
            self,
            text: str,
            callback: callable = None,
            visible: bool = True,
            enabled: bool = True,
            checked: Optional[bool] = None,
    ):
        """
        One-call function to add new menu item
        """

        item = super().addAction(text)
        item.setEnabled(enabled)

        if not visible:
            item.setVisible(False)

        if checked is not None:
            item.setCheckable(True)
            item.setChecked(checked)

        if callback:
            # noinspection PyUnresolvedReferences
            item.triggered.connect(callback)

        self._sections[-1].append(item)
        return item

    def addAction(self, *_):
        raise NotImplementedError("use add_item")

    def addActions(self, *_):
        raise NotImplementedError("use add_item")

    def addSeparator(self):
        raise NotImplementedError("use add_separator")

    def addMenu(self, *_):
        raise NotImplementedError("use add_menu")
