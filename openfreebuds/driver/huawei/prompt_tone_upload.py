"""充电盒自定义提示音上传（proto1 0x2BB6 / proto2 0x09xx）。

协议来源：APK cp/r + ap/g 反编译标定。两套协议并存：
    proto1：query(01 01 01) → ready(type1/100000) → start(02 04 <size4LE> 03 01 <equip>)
            → negotiate(type2) → 8 包滑窗 04 02 <len> 数据 → bitmap(type3) → progress(type5)
            → final(type6, result=1)。
    proto2：0901 文件信息 → 0902 会话参数 → 0904 数据 → 0909 会话结束。

FreeClip 2 真机标定（2026-11-13）：
- proto1 query 无论 5 字节还是 6 字节都只返回 tag127=100003，设备从不发 type1 ready；
  proto1 通道在该固件上整条不可用。
- proto2 `09 01` 能拿到 tag127=100000（就绪），但回复与请求里的声明大小无关；
  `09 02` 只接受裸帧（带任何尺寸 TLV 都不回）；`09 04` 四种内层布局全部无响应，
  连发 8/16 包也不回位图；`09 09` 会触发 `09 03`（已接收 0 / 总 7680）。
  结论：proto2 尚未真正建立"文件会话"，数据面不通。
"""
import asyncio
import struct
from dataclasses import dataclass, field

from openfreebuds.driver.huawei.constants import CMD_TONE_TRANSFER
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.driver.huawei.prompt_tone import crc16_xmodem
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbHuaweiToneUpload")

RESULT_READY = 100000
RESULT_SUCCESS = 1
STEP_TIMEOUT = 10
WINDOW = 8
DEFAULT_PACKET_SIZE = 240

# proto2 命令字
CMD_P2_FILE_INFO = bytes.fromhex("0901")
CMD_P2_SESSION_START = bytes.fromhex("0902")
CMD_P2_FILE_STATUS = bytes.fromhex("0903")
CMD_P2_DATA = bytes.fromhex("0904")
CMD_P2_PROGRESS = bytes.fromhex("0905")
CMD_P2_COMPLETE = bytes.fromhex("0906")
CMD_P2_SESSION_END = bytes.fromhex("09090101 01")
CMD_P2_NOTIFY = bytes.fromhex("090a")

# 真机实测：0901 之前必须先读一次 feature16（0x2BB4 tag 0x10），否则设备不应答。
CMD_2BB4 = bytes.fromhex("2bb4")
READ_FEATURE16 = b"\x2b\xb4\x01\x01\x10"

# 真机抓包标定的分包参数（2026-11-14，见交接文档 §10）
PROTO2_WINDOW_BYTES = 7680
PROTO2_FRAME_BYTES = 960
PROTO2_DEFAULT_CHUNK = 969
PROTO2_CREDIT_OK = RESULT_READY
# 真机实测：feature16 读完之后立刻发 0901 会被忽略，隔 1s 才应答。
PROTO2_PRE_DELAY = 1.0
# 收完数据后等设备落盘（09 05 进度追平 + 09 06）的最长时间
PROTO2_FLUSH_TIMEOUT = 60.0


class ToneUploadError(Exception):
    """上传过程中的设备错误。"""


class ToneUploadNotReady(ToneUploadError):
    """设备未进入上传就绪态（query 未返回 type1/100000）。"""

    def __init__(self, code: int):
        self.code = code
        super().__init__(f"设备未就绪，拒绝上传（返回码 {code}）")


def frame_body(body: bytes) -> bytes:
    """body（命令字+TLV）→ 含 0x5A 头与 CRC16-XMODEM 的完整帧。"""
    framed = b"Z" + (len(body) + 1).to_bytes(2, "big") + b"\x00" + body
    return framed + crc16_xmodem(framed).to_bytes(2, "big")


def build_query() -> bytes:
    """proto1 就绪查询：2b b6 + TLV(1,1,1)。APK `Lap/g.z()` 数组声明 5 字节，
    反编译 dump 末尾多出的 00 是填充字节，真机对照也证明尾部 00 无影响。"""
    return bytes.fromhex("2bb6010101")


def build_start(size: int, equip: int = 0) -> bytes:
    """proto1 开始传输：TLV(1,1,2) + TLV(2,4,size) + TLV(3,1,equip)。
    APK `Lap/g.i(II)` 用 `util/g.g()`（4 字节小端）写 size。"""
    return bytes.fromhex("2bb60101020204") + struct.pack("<I", size) + bytes([3, 1, equip])


def build_proto2_file_info(size: int) -> bytes:
    """proto2 文件信息（真机抓包 2026-11-14 校正）：

    `09 01 01 01 01 02 02 00 00 03 01 00 06 01 04 09 04 <总长4BE> 0a 01 00`
    size 为**整个 package 的字节数**（抓包那次 0x1EF9E = 126878），大端 4 字节。
    """
    return (bytes.fromhex("0901010101020200000301000601040904")
            + struct.pack(">I", size) + bytes.fromhex("0a0100"))


def build_proto2_session_start() -> bytes:
    """proto2 会话参数查询：裸 `09 02`（带参数设备不回）。"""
    return bytes.fromhex("0902")


def build_proto2_push_start() -> bytes:
    """proto2 开始推数据：`09 09 01 01 01`（设备随后回 09 03 状态帧）。"""
    return bytes.fromhex("0909010101")


def build_proto2_data(window: int, seq: int, chunk: bytes) -> bytes:
    """proto2 数据帧（真机抓包校正，2026-11-14）：

    `09 04 | ff | 00 | 窗口基址(3B 大端) | 帧序号(1B) | 数据`
    每窗口 7680 字节 = 8 帧 × 960 字节，帧序号 0..7。
    """
    win_b = int(window).to_bytes(3, "big")
    inner = b"\xff\x00" + win_b + bytes([seq & 0xFF]) + chunk
    return CMD_P2_DATA + inner


def build_proto2_session_end() -> bytes:
    """proto2 会话结束：09 09 + TLV(1,1,1)。APK `Lap/g.y()`。"""
    return bytes.fromhex("0909010101")


def _enc_len(n: int) -> bytes:
    if n < 128:
        return bytes([0x80, n])
    return bytes([(n >> 7) | 0x80, n & 0x7F])


def build_data(offset_location: bytes, size: int, seq: int, chunk: bytes) -> bytes:
    inner = b"\xff" + offset_location + struct.pack(">H", size) + bytes([seq]) + chunk
    return bytes.fromhex("2bb601010402") + _enc_len(len(inner)) + inner


@dataclass
class ToneResponse:
    type: int = 0
    result: int = 0
    error_code: int = 0
    query_result: int = 0
    packet_data_size: int = 0
    retransmission: list[int] = field(default_factory=list)
    progress: int = 0
    equipment_type: int = 0
    mcu_type: bytes = b""
    offset_location: bytes = b""
    data_size: int = 0


def parse_response(pkg: HuaweiSppPackage | None) -> ToneResponse:
    """按 ap/g.k 分发规则解析 0x2BB6 响应：tag5=类型，tag4=类型相关数据。"""
    r = ToneResponse()
    if pkg is None:
        return r
    p = pkg.parameters
    if p.get(5):
        r.type = p[5][0]
    if len(p.get(127, b"")) == 4:
        r.query_result = int.from_bytes(p[127], "big")
    t4 = p.get(4, b"")
    if r.type in (1, 2, 6) and len(t4) == 4:
        r.result = int.from_bytes(t4, "big")
    elif r.type == 7 and len(t4) == 4:
        r.error_code = int.from_bytes(t4, "big")
    elif r.type == 5 and len(t4) == 2:
        r.equipment_type, r.progress = t4[0], t4[1]
    if r.type == 3:
        if len(p.get(1, b"")) == 2:
            r.packet_data_size = int.from_bytes(p[1], "big")
        if len(p.get(2, b"")) == 1:
            bits = p[2][0]
            r.retransmission = [(bits >> (7 - i)) & 1 for i in range(WINDOW)]
        if len(p.get(3, b"")) == 2:
            r.mcu_type = p[3]
    if len(p.get(6, b"")) >= 2:
        r.mcu_type = p[6]
    if len(p.get(3, b"")) == 4 and r.type in (1, 2):
        r.offset_location = p[3]
        r.data_size = int.from_bytes(p[3], "big")
    return r


async def upload_tone(session, package: bytes, *, progress_cb=None) -> None:
    """通过原始帧会话上传整包。session 需提供 send_framed(bytes) 与 recv(timeout)。

    成功返回 None；设备未就绪抛 ToneUploadNotReady；其它设备错误抛 ToneUploadError。
    """
    if not package:
        raise ToneUploadError("提示音数据为空")

    await session.send_framed(frame_body(build_query()))
    resp = parse_response(await session.recv(STEP_TIMEOUT))
    if not (resp.type == 1 and resp.result == RESULT_READY):
        code = resp.result or resp.query_result or resp.error_code
        raise ToneUploadNotReady(code)
    log.info(f"Tone upload ready, equip={resp.equipment_type}")

    await session.send_framed(frame_body(build_start(len(package), resp.equipment_type)))
    resp = parse_response(await session.recv(STEP_TIMEOUT))
    if resp.type == 7:
        raise ToneUploadError(f"设备报错 {resp.error_code}")
    packet_size = resp.packet_data_size or resp.data_size or DEFAULT_PACKET_SIZE
    offset_location = resp.offset_location or b"\x00\x00\x00\x00"

    total = len(package)
    offset = 0
    while offset < total:
        count = min(WINDOW, (total - offset + packet_size - 1) // packet_size)
        for i in range(count):
            start = offset + i * packet_size
            chunk = package[start:start + packet_size]
            await session.send_framed(frame_body(build_data(offset_location, len(chunk), i, chunk)))

        while True:
            resp = parse_response(await session.recv(STEP_TIMEOUT))
            if resp.type == 6:
                if resp.result == RESULT_SUCCESS:
                    if progress_cb:
                        progress_cb(100)
                    return
                raise ToneUploadError(f"上传失败 result={resp.result}")
            if resp.type == 7:
                raise ToneUploadError(f"设备报错 {resp.error_code}")
            if resp.type == 3:
                for index, received in enumerate(resp.retransmission):
                    if received:
                        continue
                    seq = WINDOW - 1 - index
                    start = offset + seq * packet_size
                    if start >= total:
                        continue
                    chunk = package[start:start + packet_size]
                    await session.send_framed(
                        frame_body(build_data(offset_location, len(chunk), seq, chunk)))
                continue
            if resp.type == 5:
                if progress_cb:
                    progress_cb(resp.progress)
                if resp.progress >= 100:
                    continue
                break
            if resp.type == 0:
                raise ToneUploadNotReady(resp.query_result)
        offset += count * packet_size

    raise ToneUploadError("数据传输结束但未收到成功确认")


# ---------------------------------------------------------------------------
# proto2（真机抓包标定版，2026-11-14）
# ---------------------------------------------------------------------------

STEP_TIMEOUT_PROTO2 = 10


def p2_tlv(pkg) -> dict[int, bytes]:
    """把 HuaweiSppPackage 的 TLV 列表整理成 {tag: bytes}。"""
    if pkg is None:
        return {}
    return {int(k): bytes(v) for k, v in pkg.parameters.items()}


def p2_received_offset(pkg) -> int | None:
    """09 03 状态帧里的「设备已接收字节数」（tag 1，4 字节大端）。"""
    tlv = p2_tlv(pkg)
    raw = tlv.get(1, b"")
    if len(raw) == 4:
        return int.from_bytes(raw, "big")
    return None


def p2_chunk_size(pkg) -> int:
    """09 02 应答里的分包大小（tag 3，2 字节大端，真机为 969）。"""
    raw = p2_tlv(pkg).get(3, b"")
    if len(raw) == 2:
        return int.from_bytes(raw, "big")
    return PROTO2_DEFAULT_CHUNK


async def upload_tone_proto2(session, package: bytes, *, progress_cb=None) -> None:
    """按官方 App 真机行为做 proto2 上传。

    session 需提供 send_framed(bytes) 与 recv(timeout)（recv 要能收到所有命令字，
    因此驱动侧应使用 raw_session_all，而不是按命令字过滤的 raw_session）。

    步骤（对照交接文档 §10.2）：
        读一次 feature16（0x2BB4 tag 0x10）唤醒会话
        → 09 01 声明总长 → 09 02 取分包参数 → 09 09 开始推流
        → 09 04 按 7680 字节窗口推 8×960 字节 → 每窗口等 09 03 ACK
        → 收尾等 09 06 完成帧。
    """
    if not package:
        raise ToneUploadError("提示音数据为空")

    total = len(package)

    # 真机实测：串口刚连上那会儿设备还在忙初始化，feature16 读会被吞掉，
    # 所以重试到拿到应答为止；拿到之后再隔 1s 才发 0901。
    for _ in range(3):
        await session.send_framed(frame_body(READ_FEATURE16))
        if await _recv_cmd(session, {CMD_2BB4}, 3.0) is not None:
            break
        await asyncio.sleep(0.5)
    else:
        raise ToneUploadError("设备未应答 feature16 读，无法开始上传")
    await asyncio.sleep(PROTO2_PRE_DELAY)

    await session.send_framed(frame_body(build_proto2_file_info(total)))
    resp = await _recv_cmd(session, {CMD_P2_FILE_INFO}, STEP_TIMEOUT_PROTO2)
    if resp is None:
        raise ToneUploadError("设备未应答 09 01（文件信息），会话未建立")
    tlv_all = p2_tlv(resp)
    # 设备应答形如 09 01 7f 04 <credit> 04 01 14 ...，拒绝时给 7f 非 100000
    credit = tlv_all.get(0x7F, b"")
    if len(credit) == 4:
        code = int.from_bytes(credit, "big")
        if code != PROTO2_CREDIT_OK:
            raise ToneUploadNotReady(code)
        log.info(f"proto2 09 01 应答 credit={code}")

    await session.send_framed(frame_body(build_proto2_session_start()))
    resp = await _recv_cmd(session, {CMD_P2_SESSION_START}, STEP_TIMEOUT_PROTO2)
    if resp is None:
        raise ToneUploadError("设备未应答 09 02（分包参数）")
    chunk_size = p2_chunk_size(resp)
    log.info(f"proto2 分包大小 {chunk_size}")

    await session.send_framed(frame_body(build_proto2_push_start()))
    await _recv_cmd(session, {CMD_P2_FILE_STATUS}, STEP_TIMEOUT_PROTO2)

    offset = 0
    while offset < total:
        window = offset
        sent_in_window = 0
        for seq in range(8):
            start = offset + seq * PROTO2_FRAME_BYTES
            if start >= total:
                break
            chunk = package[start:start + PROTO2_FRAME_BYTES]
            await session.send_framed(frame_body(build_proto2_data(window, seq, chunk)))
            sent_in_window += 1

        expect = min(total, offset + sent_in_window * PROTO2_FRAME_BYTES)
        acked = await _wait_window_ack(session, expect)
        if not acked:
            raise ToneUploadError(f"窗口 {offset} 未被耳机确认")
        offset = expect
        if progress_cb:
            # 前 50% 对应真实的数据推流（速度随音频长度变化，官方 App 也是这个观感）
            progress_cb(int(offset * 50 / total))


    # 官方抓包里设备随后发 09 06（完成帧）= 落盘成功。真机标定（2026-11-14）：
    # 数据 ACK 完设备还要按 4096 字节一档继续内部落盘，09 05 的 tag1 是「总进度上限」
    # （= 包长 ×2），只有 tag2 追平 tag1 才会补发 09 06。以前只等 3 秒就关串口，
    # 于是误判成「设备没提交」。
    state = await _wait_complete(session, progress_cb=progress_cb)
    if progress_cb:
        progress_cb(100)
    if state == "done":
        log.info("proto2 上传完成（收到 09 06）")
    elif state == "flushed":
        log.info("proto2 上传完成（09 05 进度追平总进度，未见 09 06）")
    else:
        # 没等到追平就结束，说明文件很可能只写了一半（真机上会表现为只响前半段），
        # 不能报成功，交给上层如实提示重试
        raise ToneUploadError("等待设备落盘超时，文件可能未写完整，请重试")


async def _wait_complete(session, timeout: float = PROTO2_FLUSH_TIMEOUT, *, progress_cb=None) -> str:
    """收完数据后等设备落盘：返回 "done"(追平且收到 09 06) / "flushed"(仅追平) / "timeout"。

    09 05 的 tag1 = 总进度上限（= 包长 ×2），tag2 = 当前进度。数据 ACK 完之后设备
    还会以固定档位继续推进 tag2 —— 这一段正是官方 App 后半程那个"速度恒定"的阶段
    （HCI 观感：前半程随音频长度变化，后半程匀速）。

    真机实测（2026-11-14）：09 06 会在 tag2 只走到 tag1 一半时就发出来，此时**文件还没有
    写完整**，开盖听到的只有前半段。所以 09 06 不能再当作完成信号，必须等 tag2 追平 tag1；
    追平之后再等 09 06 收尾（最多 3 秒）。
    """
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    flushed_at: float | None = None
    complete_seen = False
    last_pct = -1
    while loop.time() < deadline:
        pkg = await session.recv(max(0.1, deadline - loop.time()))
        if pkg is None:
            if flushed_at:
                return "done" if complete_seen else "flushed"
            return "timeout"
        if pkg.command_id == CMD_P2_COMPLETE:
            tlv = p2_tlv(pkg)
            complete_seen = True
            if tlv.get(2, b"\x00")[:1] not in (b"", b"\x00"):
                log.warning(f"09 06 返回非 0 结果: {tlv}")
            if flushed_at:
                return "done"
            log.info("09 06 早到，继续等落盘进度追平")
            continue
        if pkg.command_id == CMD_P2_PROGRESS:
            tlv = p2_tlv(pkg)
            total_raw, cur_raw = tlv.get(1, b""), tlv.get(2, b"")
            if len(total_raw) == 4 and len(cur_raw) == 4:
                total = int.from_bytes(total_raw, "big")
                cur = int.from_bytes(cur_raw, "big")
                log.debug(f"09 05 落盘进度 {cur}/{total}")
                if total:
                    # 后 50% 用来画落盘进度，和官方 App 的后半程对应
                    pct = 50 + int(min(1.0, cur / total) * 50)
                    if progress_cb and pct != last_pct:
                        last_pct = pct
                        progress_cb(min(99, pct))
                if total and cur >= total and flushed_at is None:
                    flushed_at = loop.time()
                    deadline = min(deadline, loop.time() + 3.0)
    if flushed_at:
        return "done" if complete_seen else "flushed"
    return "timeout"


async def _wait_window_ack(session, expect: int) -> bool:
    """等待设备把已接收偏移推进到 expect；09 05 进度帧只当心跳。"""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + STEP_TIMEOUT_PROTO2
    while loop.time() < deadline:
        resp = await session.recv(STEP_TIMEOUT_PROTO2)
        if resp is None:
            return False
        if resp.command_id == CMD_P2_COMPLETE:
            raise ToneUploadError(f"设备提前结束传输: {p2_tlv(resp)}")
        offset = p2_received_offset(resp)
        if offset is not None and offset >= expect:
            return True
    return False


async def _recv_cmd(session, cmds: set[bytes], timeout: float):
    """等指定命令字的帧，途中丢弃心跳(2BAC)等无关帧。"""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        pkg = await session.recv(max(0.1, deadline - loop.time()))
        if pkg is None:
            return None
        if pkg.command_id in cmds:
            return pkg
    return None