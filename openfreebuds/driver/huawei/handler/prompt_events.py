"""HUAWEI 0x2B7F prompt/device events.

The official ``general_prompt_config.json`` encodes Type/value pairs as TLV
parameters.  The captured IConnect application data is assumed to arrive over
SPP unchanged; this handler does not implement an IConnect transport.

Parsed events:
  ``2b 7f 02 01 01``  cleaning reminder
  ``2b 7f 05 01 01``  drop reminder
  ``2b 7f 06 01 14``  cleaning reminder cancelled (value 20)
  ``2b 7f 06 01 15``  earbud not seated correctly (value 21)

The ``2b 7f 06 02 02 00`` status packet is deliberately ignored.
"""

from openfreebuds.constants import OfbEventKind
from openfreebuds.driver.huawei.constants import (
    CMD_PROMPT_EVENT,
    PROMPT_CLEANING_CANCEL,
    PROMPT_CLEANING_MISPLACE,
    PROMPT_CLEANING_ON,
    PROMPT_DROP_ON,
    PROMPT_TLV_CLEANING,
    PROMPT_TLV_CLEANING_STATE,
    PROMPT_TLV_DROP,
)
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiPromptEventsHandler")

PROMPT_EVENT_CLEANING = "cleaning"
PROMPT_EVENT_DROP = "drop"
PROMPT_EVENT_CLEANING_CANCEL = "cleaning_cancel"
PROMPT_EVENT_CLEANING_MISPLACE = "cleaning_misplace"


def parse_prompt_event(package: HuaweiSppPackage) -> str | None:
    """Return the event name carried by a 0x2B7F package, or None."""
    if package is None or package.command_id != CMD_PROMPT_EVENT:
        return None

    cleaning = package.find_param(PROMPT_TLV_CLEANING)
    if len(cleaning) == 1 and cleaning[0] == PROMPT_CLEANING_ON:
        return PROMPT_EVENT_CLEANING

    drop = package.find_param(PROMPT_TLV_DROP)
    if len(drop) == 1 and drop[0] == PROMPT_DROP_ON:
        return PROMPT_EVENT_DROP

    state = package.find_param(PROMPT_TLV_CLEANING_STATE)
    if len(state) == 1:
        if state[0] == PROMPT_CLEANING_CANCEL:
            return PROMPT_EVENT_CLEANING_CANCEL
        if state[0] == PROMPT_CLEANING_MISPLACE:
            return PROMPT_EVENT_CLEANING_MISPLACE

    return None


class OfbHuaweiPromptEventsHandler(OfbDriverHandlerHuawei):
    """Forward 0x2B7F prompt events to the UI notification service.

    Cleaning events are enabled only for FreeClip models; the drop event is
    enabled for every model whose official config declares ``drop_detection``.
    The handler is event-only: it does not write to the device and does not
    expose a property.
    """

    handler_id = "prompt_events"
    commands = [CMD_PROMPT_EVENT]

    def __init__(self, w_cleaning: bool = True):
        self.w_cleaning = w_cleaning

    async def on_package(self, package: HuaweiSppPackage):
        event = parse_prompt_event(package)
        if event is None:
            log.debug(f"Ignoring 0x2B7F package: {package}")
            return

        if not self.w_cleaning and event in (
            PROMPT_EVENT_CLEANING,
            PROMPT_EVENT_CLEANING_CANCEL,
            PROMPT_EVENT_CLEANING_MISPLACE,
        ):
            log.debug(f"Ignoring cleaning event on a drop-only model: {event}")
            return

        log.info(f"Prompt event: {event}")
        await self.driver.changes.send_message(OfbEventKind.HUAWEI_PROMPT_EVENT, event)
