from typing import Optional

from PyQt6.QtWidgets import QWidget

from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.widget import OfbQListItem
from openfreebuds_qt.generic import IOfbQtContext


class OfbQtCommonModule(QWidget):
    def __init__(self, parent: QWidget, context: IOfbQtContext):
        super().__init__(parent)
        self.ctx = context
        self.ofb = context.ofb
        self.list_item: Optional[OfbQListItem] = None

    def retranslate_ui(self):
        pass

    async def update_ui(self, event: OfbCoreEvent):
        pass
