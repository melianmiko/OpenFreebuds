from typing import Optional

from PyQt6.QtWidgets import QWidget

from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.widget import OfbQListItem


class OfbQtCommonModule(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.list_item: Optional[OfbQListItem] = None

    def retranslate_ui(self):
        pass

    async def update_ui(self, event: OfbCoreEvent):
        pass
