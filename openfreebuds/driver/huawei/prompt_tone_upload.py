"""Charging-case custom prompt-tone upload (proto1 0x2BB6 / proto2 0x09xx).
Protocol source: calibrated from APK cp/r and ap/g decompilation. proto1: query(01 01 01) -> ready(type1/100000) -> start(02 04 <size4LE> 03 01 <equip>) -> negotiate -> data -> finish. proto2: 09 01 file info -> 09 02 session params -> 09 09 start -> 09 04 data -> 09 09 finish, with 09 03/09 05 progress and 09 06 completion. See handoff doc section 10.
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

# proto2 command byte
CMD_P2_FILE_INFO = bytes.fromhex("0901")
CMD_P2_SESSION_START = bytes.fromhex("0902")
CMD_P2_FILE_STATUS = bytes.fromhex("0903")
CMD_P2_DATA = bytes.fromhex("0904")
CMD_P2_PROGRESS = bytes.fromhex("0905")
CMD_P2_COMPLETE = bytes.fromhex("0906")
CMD_P2_SESSION_END = bytes.fromhex("09090101 01")
CMD_P2_NOTIFY = bytes.fromhex("090a")

# Measured: read feature16 (0x2BB4 tag 0x10) once before 0901, otherwise the device does not answer.
CMD_2BB4 = bytes.fromhex("2bb4")
READ_FEATURE16 = b"\x2b\xb4\x01\x01\x10"

# Chunking parameters measured from a real capture (2026-11-14, handoff doc section 10)
PROTO2_WINDOW_BYTES = 7680
PROTO2_FRAME_BYTES = 960
PROTO2_DEFAULT_CHUNK = 969
PROTO2_CREDIT_OK = RESULT_READY
# Measured: 0901 sent immediately after a feature16 read is ignored; wait 1 s before sending it.
PROTO2_PRE_DELAY = 1.0
# Maximum wait for the device to flush after all data is sent (09 05 progress catches up + 09 06)
PROTO2_FLUSH_TIMEOUT = 60.0


class ToneUploadError(Exception):
    """Device error during upload."""


class ToneUploadNotReady(ToneUploadError):
    """Device did not enter upload-ready state (query did not return type1/100000)."""

    def __init__(self, code: int):
        self.code = code
        super().__init__(f"设备未就绪，拒绝上传（返回码 {code}）")


def frame_body(body: bytes) -> bytes:
    """body (command + TLV) -> full frame with 0x5A header and CRC16-XMODEM."""
    framed = b"Z" + (len(body) + 1).to_bytes(2, "big") + b"\x00" + body
    return framed + crc16_xmodem(framed).to_bytes(2, "big")


def build_query() -> bytes:
    """proto1 ready query: 2b b6 + TLV(1,1,1).
    The APK Lap/g.z() declares 5 bytes; the extra 00 at the end of the decompiled dump is padding, and hardware testing confirms the trailing 00 has no effect.
    """
    return bytes.fromhex("2bb6010101")


def build_start(size: int, equip: int = 0) -> bytes:
    """proto1 start transfer: TLV(1,1,2) + TLV(2,4,size) + TLV(3,1,equip).
    APK Lap/g.i(II) writes size with util/g.g() (4-byte little-endian).
    """
    return bytes.fromhex("2bb60101020204") + struct.pack("<I", size) + bytes([3, 1, equip])


def build_proto2_file_info(size: int) -> bytes:
    """proto2 file info (corrected from the 2026-11-14 hardware capture):
    09 01 01 01 01 02 02 00 00 03 01 00 06 01 04 09 04 <total length 4BE> 0a 01 00
    size is the whole package length (0x1EF9E = 126878 in that capture), 4 bytes big-endian.
    """
    return (bytes.fromhex("0901010101020200000301000601040904")
            + struct.pack(">I", size) + bytes.fromhex("0a0100"))


def build_proto2_session_start() -> bytes:
    """proto2 session parameter query: bare 09 02 (the device does not answer with parameters)."""
    return bytes.fromhex("0902")


def build_proto2_push_start() -> bytes:
    """proto2 start data transfer: 09 09 01 01 01 (the device then returns a 09 03 status frame)."""
    return bytes.fromhex("0909010101")


def build_proto2_data(window: int, seq: int, chunk: bytes) -> bytes:
    """proto2 data frame (corrected from the 2026-11-14 capture):
    09 04 | ff | 00 | window base (3B BE) | frame index (1B) | data
    Each window is 7680 bytes = 8 frames x 960 bytes; frame index 0..7.
    """
    win_b = int(window).to_bytes(3, "big")
    inner = b"\xff\x00" + win_b + bytes([seq & 0xFF]) + chunk
    return CMD_P2_DATA + inner


def build_proto2_session_end() -> bytes:
    """proto2 end session: 09 09 + TLV(1,1,1). APK Lap/g.y()."""
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
    """Parse the 0x2BB6 response with the ap/g.k rules: tag5 = type, tag4 = type-specific data."""
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
    """Upload the whole package through a raw-frame session. The session must provide send_framed(bytes) and recv(timeout).
    Returns None on success; raises ToneUploadNotReady if the device is not ready and ToneUploadError for other device errors.
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
# proto2 (capture-calibrated version, 2026-11-14)
# ---------------------------------------------------------------------------

STEP_TIMEOUT_PROTO2 = 10


def p2_tlv(pkg) -> dict[int, bytes]:
    """Convert the HuaweiSppPackage TLV list into {tag: bytes}."""
    if pkg is None:
        return {}
    return {int(k): bytes(v) for k, v in pkg.parameters.items()}


def p2_received_offset(pkg) -> int | None:
    """Bytes received by the device from a 09 03 status frame (tag 1, 4-byte big-endian)."""
    tlv = p2_tlv(pkg)
    raw = tlv.get(1, b"")
    if len(raw) == 4:
        return int.from_bytes(raw, "big")
    return None


def p2_chunk_size(pkg) -> int:
    """Chunk size from the 09 02 response (tag 3, 2-byte big-endian; 969 on hardware)."""
    raw = p2_tlv(pkg).get(3, b"")
    if len(raw) == 2:
        return int.from_bytes(raw, "big")
    return PROTO2_DEFAULT_CHUNK


async def upload_tone_proto2(session, package: bytes, *, progress_cb=None) -> None:
    """Run proto2 upload using the official App behavior measured on hardware.
    The session must provide send_framed(bytes) and recv(timeout); recv must see all command bytes, so use raw_session_all instead of command-filtered raw_session. Steps (handoff doc section 10.2): read feature16 once; wait 1 s; send 09 01 file info; send 09 02; send 09 09; stream 09 04 frames; send 09 09 finish; wait for completion.
    """
    if not package:
        raise ToneUploadError("提示音数据为空")

    total = len(package)

    # Measured: right after the serial port connects the device is still initializing and feature16 reads are dropped,
    # so retry until a response arrives; then wait 1 s before sending 0901.
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
    # Device response looks like 09 01 7f 04 <credit> 04 01 14 ...; rejection returns 7f instead of 100000
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
            # First 50% represents real data streaming; speed varies with audio length, matching the official App
            progress_cb(int(offset * 50 / total))


    # In official captures the device then sends 09 06 (completion) after a successful flush. Measured 2026-11-14:
    # after data ACKs the device still flushes internally in 4096-byte steps; 09 05 tag1 is the total progress ceiling
    # (= packet length * 2); 09 06 is sent only after tag2 catches up with tag1. The old code closed the port after 3 s,
    # so it reported 'device did not commit' incorrectly.
    state = await _wait_complete(session, progress_cb=progress_cb)
    if progress_cb:
        progress_cb(100)
    if state == "done":
        log.info("proto2 上传完成（收到 09 06）")
    elif state == "flushed":
        log.info("proto2 上传完成（09 05 进度追平总进度，未见 09 06）")
    else:
        # If the wait ends before progress catches up, the file was probably only half written (only the first half plays on device),
        # so do not report success; let the caller show a retry message
        raise ToneUploadError("等待设备落盘超时，文件可能未写完整，请重试")


async def _wait_complete(session, timeout: float = PROTO2_FLUSH_TIMEOUT, *, progress_cb=None) -> str:
    """Wait for the device to flush after all data is sent: returns 'done' (progress caught up and 09 06 received), 'flushed' (progress caught up only) or 'timeout'.
    09 05 tag1 is the total progress ceiling (= packet length * 2), tag2 is current progress. After data ACKs the device advances tag2 in fixed steps; this is the constant-speed second half of the official App.
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
                    # The last 50% drives the flush progress bar, matching the official App's second half
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
    """Wait for the device's received offset to reach expect; 09 05 progress frames are only heartbeats."""
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
    """Wait for a frame with the given command, discarding unrelated frames such as the 2BAC heartbeat."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        pkg = await session.recv(max(0.1, deadline - loop.time()))
        if pkg is None:
            return None
        if pkg.command_id in cmds:
            return pkg
    return None