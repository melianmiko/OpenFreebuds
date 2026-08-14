from typing import Optional

from PyQt6.QtWidgets import QWidget

from openfreebuds import IOpenFreebuds
from openfreebuds.exceptions import OfbDriverError, OfbNoDeviceError, OfbServerDeadError
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.utils.core_event import OfbCoreEvent
from openfreebuds_qt.app.widget import OfbQListItem
from openfreebuds_qt.generic import IOfbQtApplication


log = create_logger("OfbQtCommonModule")


class OfbQtCommonModule(QWidget):
    def __init__(self, parent: QWidget, context: IOfbQtApplication):
        super().__init__(parent)
        self.ctx = context
        self.ofb = context.ofb
        self.list_item: Optional[OfbQListItem] = None

    async def update_ui(self, event: OfbCoreEvent):
        pass

    async def can_write_property(self, group: str, prop: str) -> bool:
        if await self.ofb.get_state() != IOpenFreebuds.STATE_CONNECTED:
            return False

        health = await self.ofb.get_health_report()
        handlers = set(health.get("available_store_handlers", []))
        return f"{group}//{prop}" in handlers or f"{group}//" in handlers

    async def try_set_property(self, group: str, prop: str, value: str, action_name: str) -> bool:
        if not await self.can_write_property(group, prop):
            log.warning(f"{action_name}: skip write for {group}//{prop}, device is not ready")
            return False

        try:
            await self.ofb.set_property(group, prop, value)
            return True
        except (OfbDriverError, OfbNoDeviceError, OfbServerDeadError) as exc:
            log.warning(f"{action_name}: {exc.__class__.__name__} while writing {group}//{prop}: {exc}")
            return False
