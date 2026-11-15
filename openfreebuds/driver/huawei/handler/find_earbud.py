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

# 真机标定（2026-11-14，FreeClip 2 / COM26）：
#   开响  TX 2b 5d 01 02 <side> 00   RX 2b 5d 02 02 <side> 00 + 2b 5e 02 02 <side> 00
#   停止  TX 2b 5d 01 02 <side> 01   RX 2b 5d 02 02 <side> 00 + 2b 5e 02 02 <side> 01
#   查询  TX 2b 5e 01 01 <side>      RX 2b 5e 02 02 <side> <state>
#   side：0 = 左耳，1 = 右耳，2 = 双耳；state：0 = 正在响铃，1 = 空闲
#
# 注意：`2b 5d 01 01 <side>`（单字节载荷）也会开响，且**不能停止**；
# 只有带 state 的双字节载荷才能停，别再退回单字节写法。

_PARAM_VALUE = 2

# 响铃安全上限：UI 侧点了「响铃」却忘了停时，自动停止，避免耳朵被吵
MAX_RING_SECONDS = 60


def build_find_rq(side: int, state: int) -> HuaweiSppPackage:
    """
    构造响铃/停止请求：2b 5d 01 02 <side> <state>
    """
    return HuaweiSppPackage.change_rq(CMD_FIND_EARBUD_SET, [
        (1, bytes([side, state])),
    ])


def build_find_state_rq(side: int) -> HuaweiSppPackage:
    """
    构造响铃状态查询：2b 5e 01 01 <side>
    """
    return HuaweiSppPackage.change_rq(CMD_FIND_EARBUD_STATE, [
        (1, bytes([side])),
    ])


def parse_find_state(pkg: HuaweiSppPackage) -> tuple[int, int] | None:
    """
    解析 2b 5e 02 02 <side> <state>，返回 (side, state)；不识别的包返回 None

    真机标定（2026-11-14）：仅 0x5E 的这个形态承载「响铃状态」，
    `0` = 正在响铃、`1` = 空闲。**0x5D 的 ACK 形如 2b 5d 02 02 <side> 00，
    末位是 result（成功），不是状态**，绝不能喂给本函数。
    """
    if pkg.command_id != CMD_FIND_EARBUD_STATE:
        return None
    value = pkg.find_param(_PARAM_VALUE)
    if len(value) < 2:
        return None
    return value[0], value[1]


class OfbHuaweiFindEarbudHandler(OfbDriverHandlerHuawei):
    """
    「查找耳机」handler：让耳机播放最大音量提示音，可停止（0x2B5D / 0x2B5E）
    """

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
        # 左耳在响时，双耳（side=2）状态也会把它算进 left/right，
        # 所以这里只按单耳状态拼；UI 现在只关心「有没有在响」
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
        """动作后补一次主动回读，避免漏掉设备通知导致界面状态不准。"""
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
            # 0x5D 的 ACK 会走到这里，但它末位是 result，不是状态 —— parse_find_state 已挡掉
            return
        side, state = parsed
        if side not in (FIND_EARBUD_SIDE_LEFT, FIND_EARBUD_SIDE_RIGHT):
            # 真机实测：查询 side=2 时设备回的是两条单耳帧（00/01 各一条），
            # 状态帧里不会出现 side=2，遇到就忽略，别把双耳一起改错
            log.warn(f"Unexpected find state side={side}, ignored")
            return
        self._ringing[side] = state == FIND_EARBUD_STATE_RING
        await self._publish_ringing()

    async def _send_state(self, side: int, state: int):
        # 设备对 SET 不一定回 ACK，绝不能等它（超时异常会一路冒到 Qt 把程序带崩）；
        # 动作发完即走，真实响铃状态以 0x5E 通知/回读为准
        try:
            await self.driver.send_package(
                HuaweiSppPackage.change_rq_nowait(CMD_FIND_EARBUD_SET, [
                    (1, bytes([side, state])),
                ])
            )
        except Exception:
            log.exception(f"Failed to send find_earbud side={side} state={state}")
        if state == FIND_EARBUD_STATE_RING:
            # 设备可能不回通知，先按本地意图更新，随后由 0x5E 回读纠正
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
                # 双耳都发一遍，避免只停了一侧后另一侧还在响
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

        # 动作后补一次回读（不阻塞 UI），保证状态行跟耳机真实状态一致
        asyncio.create_task(self._refresh_after_action())
        return True
