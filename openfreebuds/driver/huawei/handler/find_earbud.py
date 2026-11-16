import asyncio

from openfreebuds.driver.huawei.constants import (
    CMD_FIND_EARBUD_SET,
    CMD_FIND_EARBUD_STATE,
    FIND_EARBUD_SIDE_BOTH,
    FIND_EARBUD_SIDE_LEFT,
    FIND_EARBUD_SIDE_RIGHT,
    FIND_EARBUD_STATE_RING,
    FIND_EARBUD_STATE_STOP,
)
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiFindEarbudHandler")

# Measured 2026-11-14 on FreeClip 2 / COM26:
#   start  TX 2b 5d 01 02 <side> 00   RX 2b 5d 02 02 <side> 00 + 2b 5e 02 02 <side> 00
#   stop   TX 2b 5d 01 02 <side> 01   RX 2b 5d 02 02 <side> 00 + 2b 5e 02 02 <side> 01
#   query  TX 2b 5e 01 01 <side>      RX 2b 5e 02 02 <side> <state>
#   side: 0 = left, 1 = right, 2 = both; state: 0 = ringing, 1 = idle
#
# Note: 2b 5d 01 01 <side> (single-byte payload) also starts ringing but CANNOT stop it;
# only the two-byte payload with state can stop it, so do not fall back to the single-byte form.

_PARAM_VALUE = 2

# Ringing safety limit: if the UI starts ringing and forgets to stop, stop automatically to protect the user's ears
MAX_RING_SECONDS = 60


def build_find_rq(side: int, state: int) -> HuaweiSppPackage:
    """Build the ring/stop request: 2b 5d 01 02 <side> <state>"""
    return HuaweiSppPackage.change_rq(CMD_FIND_EARBUD_SET, [
        (1, bytes([side, state])),
    ])


def build_find_state_rq(side: int) -> HuaweiSppPackage:
    """Build the ringing-status query: 2b 5e 01 01 <side>"""
    return HuaweiSppPackage.change_rq(CMD_FIND_EARBUD_STATE, [
        (1, bytes([side])),
    ])


def parse_find_state(pkg: HuaweiSppPackage) -> tuple[int, int] | None:
    """Parse 2b 5e 02 02 <side> <state> and return (side, state); return None for unknown packets.
    Measured 2026-11-14: only this 0x5E form carries ringing state, 0 = ringing, 1 = idle. A 0x5D ACK looks like 2b 5d 02 02 <side> 00; its last byte is result (success), not state.
    """
    if pkg.command_id != CMD_FIND_EARBUD_STATE:
        return None
    value = pkg.find_param(_PARAM_VALUE)
    if len(value) < 2:
        return None
    return value[0], value[1]


class OfbHuaweiFindEarbudHandler(OfbDriverHandlerHuawei):
    """Find-earbud handler: play the loudest prompt tone on the earbuds and allow stopping (0x2B5D / 0x2B5E)."""

    handler_id = "find_earbud"
    commands = [CMD_FIND_EARBUD_SET, CMD_FIND_EARBUD_STATE]
    init_timeout = 3
    init_attempt_max = 3

    properties = [
        ("config", "find_earbud_supported"),
        ("config", "find_earbud"),
        ("state", "find_earbud_ringing"),
    ]

    def __init__(self):
        self._ringing = {FIND_EARBUD_SIDE_LEFT: False, FIND_EARBUD_SIDE_RIGHT: False}
        self._stop_task: asyncio.Task | None = None

    async def _publish_ringing(self):
        active = []
        if self._ringing[FIND_EARBUD_SIDE_LEFT]:
            active.append("left")
        if self._ringing[FIND_EARBUD_SIDE_RIGHT]:
            active.append("right")
        # When the left earbud is ringing, a both-ears (side=2) status also counts it as left/right,
        # so build state from per-ear statuses only; the UI currently only needs 'is anything ringing'
        await self.driver.put_property("state", "find_earbud_ringing", ",".join(active))

    async def _refresh_state(self):
        for side in (FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_SIDE_RIGHT):
            try:
                resp = await self.driver.send_package(build_find_state_rq(side), 1)
            except Exception:
                log.exception(f"Refresh find state side={side} failed")
                continue
            if resp is None:
                continue
            parsed = parse_find_state(resp)
            if parsed is not None and parsed[0] in self._ringing:
                self._ringing[parsed[0]] = parsed[1] == FIND_EARBUD_STATE_RING
        await self._publish_ringing()

    async def _refresh_after_action(self):
        """Re-read once after the action so a missed device notification does not leave the UI stale."""
        await asyncio.sleep(0.4)
        await self._refresh_state()

    async def on_init(self):
        supported = False
        for side in (FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_SIDE_RIGHT):
            resp = await self.driver.send_package(build_find_state_rq(side), 2)
            if resp is not None:
                supported = True
                parsed = parse_find_state(resp)
                if parsed is not None:
                    self._ringing[side] = parsed[1] == FIND_EARBUD_STATE_RING
        await self.driver.put_property("config", "find_earbud_supported",
                                       "true" if supported else "false")
        await self._publish_ringing()

    async def on_package(self, package: HuaweiSppPackage):
        parsed = parse_find_state(package)
        if parsed is None:
            # 0x5D ACKs also arrive here, but their last byte is a result, not state; parse_find_state filters them out
            return
        side, state = parsed
        if side not in (FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_SIDE_RIGHT):
            # Measured: querying side=2 returns two per-ear frames (00 and 01),
            # side=2 never appears in a state frame; ignore it instead of changing both ears incorrectly
            log.warn(f"Unexpected find state side={side}, ignored")
            return
        self._ringing[side] = state == FIND_EARBUD_STATE_RING
        await self._publish_ringing()

    async def _send_state(self, side: int, state: int):
        # The device may not ACK SET, so never wait for it; a timeout exception would propagate into Qt and crash the app;
        # fire the action and let the 0x5E notification/readback report the real ringing state
        try:
            await self.driver.send_package(
                HuaweiSppPackage.change_rq_nowait(CMD_FIND_EARBUD_SET, [
                    (1, bytes([side, state])),
                ])
            )
        except Exception:
            log.exception(f"Failed to send find_earbud side={side} state={state}")
        if state == FIND_EARBUD_STATE_RING:
            # The device may not send a notification; update locally first, then correct from 0x5E readback
            if side == FIND_EARBUD_SIDE_BOTH:
                self._ringing[FIND_EARBUD_SIDE_LEFT] = True
                self._ringing[FIND_EARBUD_SIDE_RIGHT] = True
            else:
                self._ringing[side] = True
        else:
            if side == FIND_EARBUD_SIDE_BOTH:
                self._ringing[FIND_EARBUD_SIDE_LEFT] = False
                self._ringing[FIND_EARBUD_SIDE_RIGHT] = False
            else:
                self._ringing[side] = False
        await self._publish_ringing()

    def _schedule_auto_stop(self):
        if self._stop_task is not None and not self._stop_task.done():
            self._stop_task.cancel()

        async def guard():
            try:
                await asyncio.sleep(MAX_RING_SECONDS)
                log.info("Find earbud ring timeout, stopping")
                await self.driver.set_property("config", "find_earbud", "stop")
            except asyncio.CancelledError:
                pass
            except Exception:
                log.exception("Auto-stop of find earbud ring failed")

        self._stop_task = asyncio.create_task(guard())

    async def set_property(self, group: str, prop: str, value: str):
        if group != "config" or prop != "find_earbud":
            return False

        action = (value or "").strip().lower()
        verb, _, side = action.partition(":")
        side = side or "both"
        side_id = {"left": FIND_EARBUD_SIDE_LEFT,
                   "right": FIND_EARBUD_SIDE_RIGHT,
                   "both": FIND_EARBUD_SIDE_BOTH}.get(side)
        if side_id is None:
            log.warn(f"Unknown find_earbud side: {value}")
            return False

        if verb == "stop":
            if self._stop_task is not None and not self._stop_task.done():
                self._stop_task.cancel()
            if side_id == FIND_EARBUD_SIDE_BOTH:
                # Send to both ears so stopping one side does not leave the other ringing
                await self._send_state(FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_STATE_STOP)
                await self._send_state(FIND_EARBUD_SIDE_RIGHT, FIND_EARBUD_STATE_STOP)
            else:
                await self._send_state(side_id, FIND_EARBUD_STATE_STOP)
        elif verb == "ring":
            await self._send_state(side_id, FIND_EARBUD_STATE_RING)
            self._schedule_auto_stop()
        else:
            log.warn(f"Unknown find_earbud action: {value}")
            return False

        # Re-read once after the action without blocking the UI so the status line matches the earbuds
        asyncio.create_task(self._refresh_after_action())
        return True
