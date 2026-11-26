import webbrowser

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QTreeWidgetItem

from openfreebuds.driver.utils import get_display_device_names
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.constants import LINK_WEBSITE, LINK_GITHUB
from openfreebuds_qt.designer.about_module import Ui_OfbQtAboutModule
from openfreebuds_qt.version_info import VERSION, LIBRARIES


class OfbQtAboutModule(Ui_OfbQtAboutModule, OfbQtCommonModule):
    # The official i18n name of the Collector's Edition is 'FreeClip 2 S'; only Chinese uses 'Collector's Edition'.
    # Both names point to the same driver in the driver table, so the list must merge them into one entry.
    _MODEL_NAME_ALIASES = {
        "HUAWEI FreeClip 2 典藏版": "HUAWEI FreeClip 2 S",
        "HUAWEI FreeClip 2 S": "HUAWEI FreeClip 2 S",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.version_view.setText(VERSION)

        # Copyright label setup
        self.copyright_label.setOpenExternalLinks(True)

        # Supported devices tree
        devices = QTreeWidgetItem(None, [self.tr("Supported devices")])
        seen_names = set()
        for name in get_display_device_names():
            if name.startswith("Debug"):
                continue

            canonical = self._MODEL_NAME_ALIASES.get(name, name)
            localized = self.tr(canonical)
            if localized in seen_names:
                continue
            seen_names.add(localized)
            devices.addChild(QTreeWidgetItem(devices, [localized]))

        # Using libraries list
        dependencies = QTreeWidgetItem(None, [self.tr("Libraries")])
        for row in LIBRARIES:
            name = row.split(";")[0]
            dependencies.addChild(QTreeWidgetItem(dependencies, [name]))

        self.tree.addTopLevelItems([
            devices,
            dependencies
        ])
        self.tree.expandItem(devices)

    @pyqtSlot()
    def open_website(self):
        webbrowser.open(LINK_WEBSITE)

    @pyqtSlot()
    def open_github(self):
        webbrowser.open(LINK_GITHUB)
