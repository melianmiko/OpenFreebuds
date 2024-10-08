from typing import Optional

from PyQt6.QtWidgets import QWidget

from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.widget import OfbQListItem
from openfreebuds_qt.generic import IOfbQtApplication


class OfbQtCommonModule(QWidget):
    def __init__(self, parent: QWidget, context: IOfbQtApplication):
        super().__init__(parent)
        self.ctx = context
        self.ofb = context.ofb
        self.list_item: Optional[OfbQListItem] = None

    async def update_ui(self, event: OfbCoreEvent):
        pass
