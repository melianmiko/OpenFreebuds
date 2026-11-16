"""Charging-case tone handler tests (0x2BB1 master switch / 0x2B25 in-case / 0x2BB4 feature 16 lid-open tone).
Protocol based on 2026-11-13 FreeClip 2 calibration: 0x2BB1 read 02 00 03 00 -> p2=switch p3=supported; write 01 01 <0/1>. 0x2B25: p1=left worn p2=right worn p3=left in case p4=right in case. 0x2BB4 feature 16 payload is 12 bytes.
"""

import pytest

from openfreebuds.driver.huawei.constants import (
    CMD_BOX_TONE,
    CMD_BOX_TONE_INFO,
    CMD_MBB_FEATURE,
    MBB_FEATURE_BOX_TONE,
)
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiBoxToneHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage

TONE_STATE_RQ = HuaweiSppPackage.read_rq(CMD_BOX_TONE, [2, 3]).to_bytes()
# switch=1, supported=1
TONE_STATE_RESP = HuaweiSppPackage.change_rq(CMD_BOX_TONE, [(2, b"\x01"), (3, b"\x01")]).to_bytes()
TONE_STATE_RESP_OFF = HuaweiSppPackage.change_rq(CMD_BOX_TONE, [(2, b"\x00"), (3, b"\x01")]).to_bytes()

TONE_INFO_RQ = HuaweiSppPackage.read_rq(CMD_BOX_TONE_INFO, [1, 2, 3, 4]).to_bytes()
# both earbuds in the case
TONE_INFO_RESP_IN_BOX = HuaweiSppPackage.change_rq(
    CMD_BOX_TONE_INFO, [(1, b"\x00"), (2, b"\x00"), (3, b"\x01"), (4, b"\x01")]
).to_bytes()
# both earbuds worn (not in the case)
TONE_INFO_RESP_OUT = HuaweiSppPackage.change_rq(
    CMD_BOX_TONE_INFO, [(1, b"\x01"), (2, b"\x01"), (3, b"\x00"), (4, b"\x00")]
).to_bytes()

MBB_READ_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, b"")]
).to_bytes()
# Device baseline payload: b0=01 b1=01 b2=07
F16_PAYLOAD = bytes.fromhex("010107020000000000006d01")
MBB_READ_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, F16_PAYLOAD)]
).to_bytes()
# Payload shorter than 12 bytes -> lid-open tone not supported
MBB_SHORT_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, b"\x01\x01")]
).to_bytes()

MASTER_OFF_RQ = HuaweiSppPackage.change_rq(CMD_BOX_TONE, [(1, 0)]).to_bytes()
# Full write: b1=0 (disable lid-open), b0 synced to 1 from the current master switch
LID_OFF_PAYLOAD = bytes.fromhex("010007020000000000006d01")
LID_OFF_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, LID_OFF_PAYLOAD)]
).to_bytes()
LID_OFF_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, LID_OFF_PAYLOAD)]
).to_bytes()
# Full write: b2=0x0a=10 (volume, range 0-15)
VOL_10_PAYLOAD = bytes.fromhex("01010a020000000000006d01")
VOL_10_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, VOL_10_PAYLOAD)]
).to_bytes()
VOL_10_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, VOL_10_PAYLOAD)]
).to_bytes()


def base_model():
    return {
        TONE_STATE_RQ: [TONE_STATE_RESP],
        TONE_INFO_RQ: [TONE_INFO_RESP_IN_BOX],
        MBB_READ_RQ: [MBB_READ_RESP],
    }


async def create_driver(model):
    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiBoxToneHandler()],
        package_response_model=model,
    )
    await driver.start()
    return driver


@pytest.mark.asyncio
async def test_refresh_reads_feature16_from_device():
    driver = await create_driver(base_model())
    driver.package_log = []

    ok = await driver.set_property("config", "box_tone_refresh", "1")

    assert ok is True
    assert driver.package_log[0] == ('send', MBB_READ_RQ)
    assert await driver.get_property("config", "box_tone_id") == "109"


@pytest.mark.asyncio
async def test_init_supported():
    driver = await create_driver(base_model())
    config = await driver.get_property("config", None)
    state = await driver.get_property("state", None)

    assert config["box_tone_supported"] == "true"
    assert config["box_tone_enabled"] == "true"
    assert config["box_tone_lid_supported"] == "true"
    assert config["box_tone_lid_enabled"] == "true"
    assert config["box_tone_lid_volume"] == "7"
    assert state["headset_in_box"] == "true"


@pytest.mark.asyncio
async def test_write_master_off():
    model = base_model()
    model[MASTER_OFF_RQ] = [TONE_STATE_RESP_OFF]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_enabled", "false")
    assert result is True
    assert await driver.get_property("config", "box_tone_enabled") == "false"


@pytest.mark.asyncio
async def test_write_lid_toggle_off():
    model = base_model()
    model[LID_OFF_RQ] = [LID_OFF_RESP]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_lid_enabled", "false")
    assert result is True
    assert await driver.get_property("config", "box_tone_lid_enabled") == "false"


@pytest.mark.asyncio
async def test_write_lid_volume():
    model = base_model()
    model[VOL_10_RQ] = [VOL_10_RESP]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_lid_volume", "10")
    assert result is True
    assert await driver.get_property("config", "box_tone_lid_volume") == "10"


@pytest.mark.asyncio
async def test_write_lid_volume_out_of_range():
    driver = await create_driver(base_model())

    assert await driver.set_property("config", "box_tone_lid_volume", "16") is False
    assert await driver.set_property("config", "box_tone_lid_volume", "50") is False
    assert await driver.get_property("config", "box_tone_lid_volume") == "7"


@pytest.mark.asyncio
async def test_write_requires_in_box():
    model = base_model()
    model[TONE_INFO_RQ] = [TONE_INFO_RESP_OUT]
    driver = await create_driver(model)
    assert await driver.get_property("state", "headset_in_box") == "false"

    assert await driver.set_property("config", "box_tone_enabled", "false") is False
    assert await driver.set_property("config", "box_tone_lid_enabled", "false") is False


@pytest.mark.asyncio
async def test_lid_unsupported_short_payload():
    model = base_model()
    model[MBB_READ_RQ] = [MBB_SHORT_RESP]
    driver = await create_driver(model)

    assert await driver.get_property("config", "box_tone_lid_supported") == "false"
    assert await driver.set_property("config", "box_tone_lid_enabled", "false") is False


# Write tone id: full write to p2, b9..b10=big-endian toneId, b11=select=1;
# devId keeps the value reported by the device from the cached payload (the earbud MAC on hardware), not recomputed from toneId.
# Built-in tone id=18(0x12); devId keeps the baseline 020000000000
BUILTIN_ID_PAYLOAD = bytes.fromhex("010107020000000000001201")
BUILTIN_ID_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, BUILTIN_ID_PAYLOAD)]
).to_bytes()
BUILTIN_ID_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, BUILTIN_ID_PAYLOAD)]
).to_bytes()
# Custom tone id=109(0x6d); devId also keeps the baseline
CUSTOM_ID_PAYLOAD = bytes.fromhex("010107020000000000006d01")
CUSTOM_ID_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, CUSTOM_ID_PAYLOAD)]
).to_bytes()
CUSTOM_ID_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, CUSTOM_ID_PAYLOAD)]
).to_bytes()


@pytest.mark.asyncio
async def test_readback_tone_id():
    driver = await create_driver(base_model())

    assert await driver.get_property("config", "box_tone_id") == "109"
    assert await driver.get_property("config", "box_tone_device_id") == "020000000000"


@pytest.mark.asyncio
async def test_write_tone_id_builtin():
    model = base_model()
    model[BUILTIN_ID_RQ] = [BUILTIN_ID_RESP]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_id", "18")
    assert result is True
    assert await driver.get_property("config", "box_tone_id") == "18"
    assert await driver.get_property("config", "box_tone_device_id") == "020000000000"


@pytest.mark.asyncio
async def test_write_tone_id_custom():
    model = base_model()
    model[CUSTOM_ID_RQ] = [CUSTOM_ID_RESP]
    driver = await create_driver(model)

    result = await driver.set_property("config", "box_tone_id", "109")
    assert result is True
    assert await driver.get_property("config", "box_tone_id") == "109"
    assert await driver.get_property("config", "box_tone_device_id") == "020000000000"


@pytest.mark.asyncio
async def test_write_tone_id_out_of_range():
    driver = await create_driver(base_model())

    assert await driver.set_property("config", "box_tone_id", "70000") is False
    assert await driver.set_property("config", "box_tone_id", "-1") is False
    assert await driver.set_property("config", "box_tone_id", "abc") is False
    assert await driver.get_property("config", "box_tone_id") == "109"


# Device semantics of select (measured 2026-11-13): 0=built-in fixed tone (only id 0 'Unfold'), 1=uploaded audio
DEFAULT_TONE_PAYLOAD = bytes.fromhex("010107020000000000000000")
DEFAULT_TONE_RQ = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, DEFAULT_TONE_PAYLOAD)]
).to_bytes()
DEFAULT_TONE_RESP = HuaweiSppPackage.change_rq(
    CMD_MBB_FEATURE, [(1, b"\x10"), (2, DEFAULT_TONE_PAYLOAD)]
).to_bytes()


@pytest.mark.asyncio
async def test_write_tone_id_zero_selects_builtin():
    """Selecting built-in 'Unfold' (id 0) must write select=0, otherwise the device keeps playing the last uploaded audio."""
    model = base_model()
    model[DEFAULT_TONE_RQ] = [DEFAULT_TONE_RESP]
    driver = await create_driver(model)

    assert await driver.set_property("config", "box_tone_id", "0") is True
    assert await driver.get_property("config", "box_tone_id") == "0"
    assert (await driver.get_property("config", "box_tone_upload_status")) == "builtin"


@pytest.mark.asyncio
async def test_upload_zero_is_skipped():
    """Id 0 is a real built-in tone; the upload request writes feature16 only and never streams audio."""
    import json
    model = base_model()
    model[DEFAULT_TONE_RQ] = [DEFAULT_TONE_RESP]
    driver = await create_driver(model)

    request = json.dumps({"id": 0, "path": "does-not-exist.pcm", "name": "unfold"})
    assert await driver.set_property("config", "box_tone_upload", request) is True
    assert (await driver.get_property("config", "box_tone_upload_status")) == "builtin"
    commands = [entry[1][6:8] for entry in driver.package_log if entry[0] == "send"]
    assert b"\x09\x01" not in commands and b"\x09\x02" not in commands


@pytest.mark.asyncio
async def test_tone_id_switch_clears_status():
    """Selecting an id only changes the slot and no longer reports 'audio not uploaded'; switching back to id 0 shows the built-in state."""
    id55_payload = bytes.fromhex("010107020000000000003701")
    id0_payload = bytes.fromhex("010107020000000000000000")
    model = base_model()
    model[DEFAULT_TONE_RQ] = [DEFAULT_TONE_RESP]
    model[HuaweiSppPackage.change_rq(
        CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, id55_payload)]).to_bytes()] = [
        HuaweiSppPackage.change_rq(
            CMD_MBB_FEATURE, [(1, b"\x10"), (2, id55_payload)]).to_bytes()]
    model[HuaweiSppPackage.change_rq(
        CMD_MBB_FEATURE, [(1, MBB_FEATURE_BOX_TONE), (2, id0_payload)]).to_bytes()] = [
        HuaweiSppPackage.change_rq(
            CMD_MBB_FEATURE, [(1, b"\x10"), (2, id0_payload)]).to_bytes()]
    driver = await create_driver(model)

    assert await driver.set_property("config", "box_tone_id", "55") is True
    assert (await driver.get_property("config", "box_tone_upload_status")) == ""

    assert await driver.set_property("config", "box_tone_id", "0") is True
    assert (await driver.get_property("config", "box_tone_upload_status")) == "builtin"


@pytest.mark.asyncio
async def test_write_lid_volume_no_ack_keeps_local(monkeypatch):
    """Do not throw TimeoutError to the UI when a 0x2BB4 write gets no ACK (common on FreeClip 2)."""
    from openfreebuds.driver.huawei.handler import config_box_tone

    monkeypatch.setattr(config_box_tone, "_F16_WRITE_TIMEOUT", 0.2)
    monkeypatch.setattr(config_box_tone, "_MBB_READ_TIMEOUT", 0.2)

    model = base_model()  # Deliberately return no response to VOL_10_RQ
    driver = await create_driver(model)

    assert await driver.set_property("config", "box_tone_lid_volume", "10") is True
    # Write gets no response; readback still returns the device-reported 7 -> the UI trusts the device
    assert await driver.get_property("config", "box_tone_lid_volume") == "7"


@pytest.mark.asyncio
async def test_write_lid_volume_no_ack_and_no_reread(monkeypatch):
    """No response from write or readback: do not raise; keep the local value."""
    from openfreebuds.driver.huawei.handler import config_box_tone

    monkeypatch.setattr(config_box_tone, "_F16_WRITE_TIMEOUT", 0.2)
    monkeypatch.setattr(config_box_tone, "_MBB_READ_TIMEOUT", 0.2)

    model = base_model()
    driver = await create_driver(model)
    # After initialization, also block readback to simulate a sleeping case where the whole link is silent
    model[MBB_READ_RQ] = []

    assert await driver.set_property("config", "box_tone_lid_volume", "10") is True
    assert await driver.get_property("config", "box_tone_lid_volume") == "7"


@pytest.mark.asyncio
async def test_write_lid_volume_same_value_skipped():
    """Dragging to the original value must not disturb the earbuds."""
    model = base_model()
    driver = await create_driver(model)
    before = len(driver.package_log)

    assert await driver.set_property("config", "box_tone_lid_volume", "7") is True
    assert len(driver.package_log) == before


@pytest.mark.asyncio
async def test_tone_upload_property_is_registered():
    """The GUI writes an upload request to config/box_tone_upload; an unregistered handler raises FbMissingHandlerError."""
    import json

    from openfreebuds.driver.huawei.handler.config_box_tone import OfbHuaweiBoxToneHandler

    assert ("config", "box_tone_upload") in OfbHuaweiBoxToneHandler.properties

    driver = await create_driver(base_model())
    request = json.dumps({"id": 109, "path": "missing.pcm", "name": "tone"})

    assert await driver.set_property("config", "box_tone_upload", request) is False
    # Missing file -> status code file_missing, translated by the UI
    assert await driver.get_property("config", "box_tone_upload_status") == "file_missing"


@pytest.mark.asyncio
async def test_tone_upload_without_payload_is_unsupported():
    """Do not upload blindly without a feature 16 payload; report unsupported."""
    import json

    model = base_model()
    model[MBB_READ_RQ] = []  # Device does not answer feature 16
    driver = await create_driver(model)

    request = json.dumps({"id": 109, "path": "any.pcm", "name": "tone"})
    assert await driver.set_property("config", "box_tone_upload", request) is False
    assert await driver.get_property("config", "box_tone_upload_status") == "unsupported"
