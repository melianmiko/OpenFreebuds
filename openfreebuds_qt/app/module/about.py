import webbrowser

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QTreeWidgetItem

from openfreebuds import DEVICE_TO_DRIVER_MAP
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.constants import LINK_WEBSITE, LINK_GITHUB, ASSETS_PATH
from openfreebuds_qt.designer.about_module import Ui_OfbQtAboutModule
from openfreebuds_qt.version_info import VERSION


class OfbQtAboutModule(Ui_OfbQtAboutModule, OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.version_view.setText(VERSION)

        # Supported devices tree
        devices = QTreeWidgetItem(None, [self.tr("Supported devices")])
        for name in DEVICE_TO_DRIVER_MAP.keys():
            if name.startswith("Debug"):
                continue
            devices.addChild(QTreeWidgetItem(devices, [name]))

        # Using libraries list
        dependencies = QTreeWidgetItem(None, [self.tr("Libraries")])
        with open(ASSETS_PATH / "dependencies.txt", "r") as f:
            for row in f.read().split("\n"):
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

    def retranslate_ui(self):
        self.retranslateUi(self)
