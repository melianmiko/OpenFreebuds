import pytest

from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.driver.huawei.prompt_tone_upload import (
    RESULT_READY,
    ToneUploadError,
    ToneUploadNotReady,
    build_data,
    build_proto2_data,
    build_proto2_file_info,
    build_proto2_push_start,
    build_proto2_session_end,
    build_proto2_session_start,
    build_query,
    build_start,
    frame_body,
    parse_response,
    READ_FEATURE16,
    upload_tone,
    upload_tone_proto2,
)


def _pkg(params: dict) -> HuaweiSppPackage:
    return HuaweiSppPackage(b"\x2b\xb6", list(params.items()))


def _ready():
    return _pkg({5: b"\x01", 4: RESULT_READY.to_bytes(4, "big")})


def _query_100003():
    return _pkg({127: (100003).to_bytes(4, "big")})


def _negotiate():
    return _pkg({5: b"\x02", 4: RESULT_READY.to_bytes(4, "big"), 3: b"\x00\x00\x00\x00"})


def _final(result=1):
    return _pkg({5: b"\x06", 4: result.to_bytes(4, "big")})


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.sent = []

    async def send_framed(self, framed):
        self.sent.append(framed)

    async def recv(self, timeout=5):
        if self._responses:
            return self._responses.pop(0)
        return None


def test_build_query():
    assert build_query() == bytes.fromhex("2bb6010101")


def test_build_start():
    # APK writes size as 4-byte little-endian: 16000 -> 80 3e 00 00
    assert build_start(16000, 0) == bytes.fromhex("2bb60101020204803e0000030100")


def test_build_proto2_file_info():
    """2026-11-14 hardware capture: total length is 4-byte big-endian (0x1EF9E in that capture)."""
    body = build_proto2_file_info(0x1EF9E)
    assert body == bytes.fromhex("0901010101020200000301000601040904") + b"\x00\x01\xef\x9e" + bytes.fromhex("0a0100")


def test_build_proto2_data():
    """Hardware layout: 09 04 | ff | 00 | window base (3B BE) | frame index | data."""
    body = build_proto2_data(0x1E00, 3, b"\x01\x02")
    assert body == bytes.fromhex("0904ff00") + b"\x00\x1e\x00" + b"\x03" + b"\x01\x02"


def test_proto2_frame_lengths():
    """960 data bytes + 8-byte header = 968, exactly the SPP frame payload length on hardware."""
    chunk = b"\x00" * 960
    assert len(build_proto2_data(0, 0, chunk)) == 968


def test_build_proto2_session_end():
    assert build_proto2_session_end() == bytes.fromhex("0909010101")
    assert build_proto2_push_start() == bytes.fromhex("0909010101")
    assert build_proto2_session_start() == bytes.fromhex("0902")


def test_frame_body_crc():
    framed = frame_body(build_query())
    assert framed[0:1] == b"Z"
    assert int.from_bytes(framed[1:3], "big") == len(build_query()) + 1


def test_build_data_small_len():
    body = build_data(b"\x00\x00\x00\x00", 4, 0, b"\x01\x02\x03\x04")
    assert body[:6] == bytes.fromhex("2bb601010402")
    assert body[6:8] == bytes([0x80, 12])


def test_parse_query_100003():
    r = parse_response(_query_100003())
    assert r.type == 0
    assert r.query_result == 100003


def test_parse_ready():
    r = parse_response(_ready())
    assert r.type == 1
    assert r.result == RESULT_READY


def test_parse_bitmap():
    r = parse_response(_pkg({5: b"\x03", 1: (240).to_bytes(2, "big"), 2: b"\xfe"}))
    assert r.type == 3
    assert r.packet_data_size == 240
    assert r.retransmission == [1, 1, 1, 1, 1, 1, 1, 0]


def test_parse_progress():
    r = parse_response(_pkg({5: b"\x05", 4: bytes([0, 50])}))
    assert r.type == 5
    assert r.progress == 50


@pytest.mark.asyncio
async def test_upload_not_ready_100003():
    session = FakeSession([_query_100003()])
    with pytest.raises(ToneUploadNotReady) as ei:
        await upload_tone(session, b"\x00" * 600)
    assert ei.value.code == 100003
    assert len(session.sent) == 1


@pytest.mark.asyncio
async def test_upload_not_ready_timeout():
    session = FakeSession([])
    with pytest.raises(ToneUploadNotReady):
        await upload_tone(session, b"\x00" * 600)


@pytest.mark.asyncio
async def test_upload_success():
    session = FakeSession([_ready(), _negotiate(), _final(1)])
    progress = []
    await upload_tone(session, b"\x00" * 600, progress_cb=progress.append)
    assert progress[-1] == 100
    assert session.sent[0] == frame_body(build_query())
    assert session.sent[1] == frame_body(build_start(600, 0))


@pytest.mark.asyncio
async def test_upload_final_failure():
    session = FakeSession([_ready(), _negotiate(), _final(0)])
    with pytest.raises(ToneUploadError):
        await upload_tone(session, b"\x00" * 600)


@pytest.mark.asyncio
async def test_upload_empty_package():
    session = FakeSession([_ready()])
    with pytest.raises(ToneUploadError):
        await upload_tone(session, b"")


# ---------------------------------------------------------------------------
# proto2 upload (based on the official App capture on 2026-11-14)
# ---------------------------------------------------------------------------

def _p2_feature16():
    return HuaweiSppPackage(b"\x2b\xb4", [(1, b"\x10"), (2, b"\x01\x01\x03\x02\x00\x00\x00\x00\x00\x00\x64\x01")])


def _p2_info(credit=100000):
    return HuaweiSppPackage(b"\x09\x01", [(0x7F, credit.to_bytes(4, "big"))])


def _p2_notify():
    return HuaweiSppPackage(b"\x09\x0a", [(1, b"\x01")])


def _p2_params(chunk=969):
    return HuaweiSppPackage(b"\x09\x02", [(3, chunk.to_bytes(2, "big")), (1, (150).to_bytes(2, "big"))])


def _p2_status(offset):
    return HuaweiSppPackage(b"\x09\x03", [(1, offset.to_bytes(4, "big")),
                                         (2, (7680).to_bytes(4, "big")),
                                         (5, b"\x02")])


def _p2_progress(offset):
    return HuaweiSppPackage(b"\x09\x05", [(1, offset.to_bytes(4, "big")),
                                         (2, (7680).to_bytes(4, "big")),
                                         (3, b"\x64")])


@pytest.mark.asyncio
async def test_proto2_upload_single_window():
    """2000 bytes = one incomplete window (960+960+80); finish after the ACK."""
    session = FakeSession([_p2_feature16(), _p2_info(), _p2_notify(), _p2_params(), _p2_status(0), _p2_status(2000), _p2_flush(2000), _p2_complete()])
    progress = []
    await upload_tone_proto2(session, b"\x00" * 2000, progress_cb=progress.append)
    assert progress[-1] == 100
    # The first frame must be a feature16 read; measured: without it, 0901 is not answered
    assert session.sent[0] == frame_body(READ_FEATURE16)
    assert session.sent[1] == frame_body(build_proto2_file_info(2000))
    assert session.sent[2] == frame_body(build_proto2_session_start())
    assert session.sent[3] == frame_body(build_proto2_push_start())
    data = session.sent[4:]
    assert len(data) == 3
    assert data[0] == frame_body(build_proto2_data(0, 0, b"\x00" * 960))
    assert data[1] == frame_body(build_proto2_data(0, 1, b"\x00" * 960))
    assert data[2] == frame_body(build_proto2_data(0, 2, b"\x00" * 80))


@pytest.mark.asyncio
async def test_proto2_upload_two_windows():
    """Full 7680-byte window + remainder: the second window base must be 0x1E00."""
    total = 7680 + 1000
    session = FakeSession([
        _p2_feature16(), _p2_info(), _p2_notify(), _p2_params(), _p2_status(0),
        _p2_progress(7680), _p2_status(7680),
        _p2_status(total), _p2_flush(total), _p2_complete(),
    ])
    await upload_tone_proto2(session, b"\x00" * total)
    data_frames = session.sent[4:]
    assert len(data_frames) == 8 + 2
    assert data_frames[8] == frame_body(build_proto2_data(0x1E00, 0, b"\x00" * 960))


@pytest.mark.asyncio
async def test_proto2_upload_refused():
    session = FakeSession([_p2_feature16(), _p2_info(100003)])
    with pytest.raises(ToneUploadNotReady) as ei:
        await upload_tone_proto2(session, b"\x00" * 100)
    assert ei.value.code == 100003


@pytest.mark.asyncio
async def test_proto2_upload_no_ack():
    """If the device does not ACK, report an error; do not pretend success."""
    session = FakeSession([_p2_feature16(), _p2_info(), _p2_notify(), _p2_params(), _p2_status(0)])
    with pytest.raises(ToneUploadError):
        await upload_tone_proto2(session, b"\x00" * 2000)

def _p2_flush(total):
    """Flush progress frame: tag1 = tag2 = packet length * 2."""
    full = total * 2
    return HuaweiSppPackage(b"\x09\x05", [(1, full.to_bytes(4, "big")),
                                         (2, full.to_bytes(4, "big")),
                                         (3, b"\x64")])


def _p2_complete():
    return HuaweiSppPackage(b"\x09\x06", [(1, b"\x01"), (2, b"\x00"), (3, b"\x02")])


@pytest.mark.asyncio
async def test_proto2_complete_before_flush_is_not_done():
    """An early 09 06 (only half of tag1) is not completion; keep waiting for tag2 to catch tag1."""
    total = 2000
    session = FakeSession([
        _p2_feature16(), _p2_info(), _p2_notify(), _p2_params(), _p2_status(0),
        _p2_status(total),
        _p2_complete(),
        _p2_flush(total),
    ])
    progress = []
    await upload_tone_proto2(session, b"\x00" * total, progress_cb=progress.append)
    assert progress[-1] == 100