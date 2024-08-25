from typing import Optional

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QWidget, QBoxLayout

from openfreebuds_qt.app.widget import OfbQListItem
from openfreebuds_qt.app.widget.list_header import OfbQListHeader


class OfbQtSettingsTabHelper:
    class Entry:
        def __init__(self, parent: QWidget, label: str, content: QWidget):
            self.label = label
            self.list_item = OfbQListItem(parent, parent.tr(label))
            self.content = content

    class Section:
        def __init__(self, parent: QWidget, label: str, index: int):
            self.label = label
            self.list_item: Optional[OfbQListHeader] = OfbQListHeader(parent, parent.tr(label)) if label else None
            self.items: list[OfbQtSettingsTabHelper.Entry] = []
            self.index: int = index

        def set_visible(self, visible: bool):
            if self.list_item is not None:
                self.list_item.setVisible(visible)
            for w in self.items:
                w.list_item.setVisible(visible)

    def __init__(self, tabs_root: QWidget, body_root: QWidget):
        self.tabs_root = tabs_root
        self.root = body_root

        self.root_layout = QBoxLayout(QBoxLayout.Direction.Down)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.root.setLayout(self.root_layout)

        self.tabs_layout = QBoxLayout(QBoxLayout.Direction.Down)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout.setSpacing(0)
        self.tabs_root.setLayout(self.tabs_layout)

        self._active_entry: Optional[OfbQtSettingsTabHelper.Entry] = None
        self._sections: list[OfbQtSettingsTabHelper.Section] = [
            OfbQtSettingsTabHelper.Section(self.tabs_root, "", 0)
        ]

    def set_active_tab(self, section: int, tab: int):
        if self._active_entry is not None:
            self._active_entry.list_item.set_active(False)
            self._active_entry.content.setVisible(False)

        new_active = self._sections[section].items[tab]
        new_active.list_item.set_active(True)
        new_active.content.setVisible(True)
        new_active.content.setFocus()

        self._active_entry = new_active

    def retranslate_ui(self):
        for section in self._sections:
            if section.list_item is not None:
                section.list_item.setText(self.root.tr(section.label))
            for item in section.items:
                item.list_item.label.setText(self.root.tr(item.label))

    def add_tab(self, label: str, content: QWidget):
        section = len(self._sections) - 1
        tab = len(self._sections[section].items)
        entry = OfbQtSettingsTabHelper.Entry(parent=self.tabs_root,
                                             label=label,
                                             content=content)

        @pyqtSlot()
        def _activate(*_):
            self.set_active_tab(section, tab)

        @pyqtSlot()
        def _kbd_activate(e: QKeyEvent):
            if e.key() in [Qt.Key.Key_Return, Qt.Key.Key_Space]:
                _activate(e)
            elif e.key() == Qt.Key.Key_Down:
                entry.list_item.focusNextChild()
            elif e.key() == Qt.Key.Key_Up:
                entry.list_item.focusPreviousChild()

        entry.list_item.label.mousePressEvent = _activate
        entry.list_item.label.keyPressEvent = _kbd_activate
        self.tabs_layout.addWidget(entry.list_item)
        self._sections[section].items.append(entry)
        self.root_layout.addWidget(content)
        content.setVisible(False)

        return entry

    def add_section(self, label: str):
        section = len(self._sections)
        entry = OfbQtSettingsTabHelper.Section(self.tabs_root, label=label, index=section)
        self.tabs_layout.addWidget(entry.list_item)
        self._sections.append(entry)
        return entry

    def finalize_list(self):
        self.tabs_layout.insertStretch(-1, 1)
        self.set_active_tab(0, 0)
