import asyncio
from pathlib import Path

import pytest

from openfreebuds.driver.huawei.constants import (
    CMD_FEATURE_ABILITY,
    CMD_FEATURE_SWITCH,
    CMD_PROMPT_TONE_OTA_DATA,
    CMD_PROMPT_TONE_OTA_ERROR,
    CMD_PROMPT_TONE_OTA_OFFSET,
    CMD_PROMPT_TONE_OTA_PREPARE,
    CMD_PROMPT_TONE_OTA_PROGRESS,
    CMD_PROMPT_TONE_OTA_READY,
    CMD_PROMPT_TONE_OTA_START,
)
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler.prompt_tone import (
    PROMPT_TONE_SUCCESS,
    OfbHuaweiPromptToneHandler,
    build_prompt_tone_package,
)
from openfreebuds.driver.huawei.package import HuaweiSppPackage


def test_huawei_package_supports_extended_tlv_lengths():
    value = bytes(range(130))
    raw = HuaweiSppPackage(CMD_PROMPT_TONE_OTA_DATA, [(9, value)]).to_bytes()
    assert b"\x09\x81\x02" in raw
    assert HuaweiSppPackage.from_bytes(raw).find_param(9) == value


def test_huawei_package_supports_raw_payloads():
    payload = b"\xff\x00\x00\x00\x00\x00abc"
    raw = HuaweiSppPackage.raw(CMD_PROMPT_TONE_OTA_DATA, payload).to_bytes()
    assert raw[4:6] == CMD_PROMPT_TONE_OTA_DATA
    assert raw[6:6 + len(payload)] == payload


@pytest.mark.asyncio
async def test_prompt_tone_reads_and_writes_box_tone_state():
    ability_rq = HuaweiSppPackage(
        CMD_FEATURE_ABILITY,
        [(1, b"\x01"), (14, b""), (21, b"")],
        resp=CMD_FEATURE_ABILITY,
    ).to_bytes()
    ability_resp = HuaweiSppPackage(CMD_FEATURE_ABILITY, [(1, b"\x00"), (21, b"\x01\x01\x02")]).to_bytes()

    read_rq = HuaweiSppPackage(CMD_FEATURE_SWITCH, [(1, 16)], resp=CMD_FEATURE_SWITCH).to_bytes()
    read_resp = HuaweiSppPackage(
        CMD_FEATURE_SWITCH,
        [(1, 16), (2, bytes.fromhex("01010f020000000000000000"))],
    ).to_bytes()

    set_volume_rq = HuaweiSppPackage.change_rq(
        CMD_FEATURE_SWITCH,
        [(1, 16), (2, bytes.fromhex("010105020000000000000000"))],
    ).to_bytes()
    set_volume_resp = HuaweiSppPackage(
        CMD_FEATURE_SWITCH,
        [(1, 16), (2, bytes.fromhex("010105020000000000000000"))],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiPromptToneHandler()],
        package_response_model={
            ability_rq: [ability_resp],
            read_rq: [read_resp],
            set_volume_rq: [set_volume_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("case_sound", "available") == "true"
    assert await driver.get_property("case_sound", "protocol") == "2"
    assert await driver.get_property("case_sound", "enabled") == "true"
    assert await driver.get_property("case_sound", "volume") == "15"

    await driver.set_property("case_sound", "volume", "5")

    assert await driver.get_property("case_sound", "volume") == "5"
    assert driver.package_log[0] == ("send", set_volume_rq)


@pytest.mark.asyncio
async def test_prompt_tone_can_transfer_ota_tone(tmp_path: Path):
    pcm_data = bytes(range(256)) + bytes(range(64))
    pcm_path = tmp_path / "Whistle.pcm"
    pcm_path.write_bytes(pcm_data)
    device_id = "AABBCCDDEEFF"
    packet_size = 160

    class FakeCache:
        def ensure_pcm(self, tone):
            return pcm_path

    ability_rq = HuaweiSppPackage(
        CMD_FEATURE_ABILITY,
        [(1, b"\x01"), (14, b""), (21, b"")],
        resp=CMD_FEATURE_ABILITY,
    ).to_bytes()
    ability_resp = HuaweiSppPackage(CMD_FEATURE_ABILITY, [(1, b"\x00"), (21, b"\x01\x01\x02")]).to_bytes()
    read_rq = HuaweiSppPackage(CMD_FEATURE_SWITCH, [(1, 16)], resp=CMD_FEATURE_SWITCH).to_bytes()
    read_resp = HuaweiSppPackage(
        CMD_FEATURE_SWITCH,
        [(1, 16), (2, bytes.fromhex("01010f020000000000000000"))],
    ).to_bytes()

    initial_package = build_prompt_tone_package(pcm_data, b"\x00\x00\x00\x00", "Whistle")
    start_rq = HuaweiSppPackage(
        CMD_PROMPT_TONE_OTA_START,
        [
            (1, b"\x01"),
            (2, b"\x00\x00"),
            (3, b"\x00"),
            (6, b"\x04"),
            (9, len(initial_package).to_bytes(4, byteorder="big")),
            (10, b"\x00"),
        ],
        resp=CMD_PROMPT_TONE_OTA_START,
    ).to_bytes()
    start_resp = HuaweiSppPackage(
        CMD_PROMPT_TONE_OTA_START,
        [(6, b"\x04"), (11, b"\x01\x02\x03\x04"), (127, PROMPT_TONE_SUCCESS.to_bytes(4, "big"))],
    ).to_bytes()

    interim_payload = bytes.fromhex(f"01010f{device_id}000000")
    interim_state_rq = HuaweiSppPackage.change_rq(CMD_FEATURE_SWITCH, [(1, 16), (2, interim_payload)]).to_bytes()
    interim_state_resp = HuaweiSppPackage(CMD_FEATURE_SWITCH, [(1, 16), (2, interim_payload)]).to_bytes()

    prepare_rq = HuaweiSppPackage(CMD_PROMPT_TONE_OTA_PREPARE, resp=CMD_PROMPT_TONE_OTA_PREPARE).to_bytes()
    prepare_resp = HuaweiSppPackage(
        CMD_PROMPT_TONE_OTA_PREPARE,
        [(3, (packet_size + 9).to_bytes(2, byteorder="big"))],
    ).to_bytes()
    ready_rq = HuaweiSppPackage(CMD_PROMPT_TONE_OTA_READY, [(1, 1)], resp=CMD_PROMPT_TONE_OTA_OFFSET).to_bytes()
    offset_resp = HuaweiSppPackage(
        CMD_PROMPT_TONE_OTA_OFFSET,
        [(1, b"\x00\x00\x00\x00"), (2, b"\x00\x00\x00\x00"), (3, b"\x00")],
    ).to_bytes()

    transfer_package = build_prompt_tone_package(pcm_data, b"\x01\x02\x03\x04", "Whistle")
    first_data_payload = b"\xff\x00\x00\x00\x00\x00" + transfer_package[:packet_size]
    first_data_rq = HuaweiSppPackage.raw(CMD_PROMPT_TONE_OTA_DATA, first_data_payload).to_bytes()
    progress_resp = HuaweiSppPackage(
        CMD_PROMPT_TONE_OTA_PROGRESS,
        [(1, len(transfer_package).to_bytes(4, "big")), (2, len(transfer_package).to_bytes(4, "big"))],
    ).to_bytes()

    final_payload = bytes.fromhex(f"01010f{device_id}002b01")
    final_state_rq = HuaweiSppPackage.change_rq(CMD_FEATURE_SWITCH, [(1, 16), (2, final_payload)]).to_bytes()
    final_state_resp = HuaweiSppPackage(CMD_FEATURE_SWITCH, [(1, 16), (2, final_payload)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiPromptToneHandler(
                cache=FakeCache(),
                device_id_provider=lambda: device_id,
                transfer_settle_delay=0,
            )
        ],
        package_response_model={
            ability_rq: [ability_resp],
            read_rq: [read_resp],
            start_rq: [start_resp],
            interim_state_rq: [interim_state_resp],
            prepare_rq: [prepare_resp],
            ready_rq: [offset_resp],
            first_data_rq: [progress_resp],
            final_state_rq: [final_state_resp],
        },
    )

    await driver.start()
    await driver.set_property("case_sound", "tone_id", "43")

    assert await driver.get_property("case_sound", "tone_id") == "43"
    assert await driver.get_property("case_sound", "tone_select") == "1"
    assert await driver.get_property("case_sound", "transfer_progress") == "100"
    assert await driver.get_property("case_sound", "transfer_status") == "ready"
    assert ("send", first_data_rq) in driver.package_log


@pytest.mark.asyncio
async def test_prompt_tone_queues_ota_error_responses():
    handler = OfbHuaweiPromptToneHandler()
    handler._ota_queue = asyncio.Queue()
    error = HuaweiSppPackage(CMD_PROMPT_TONE_OTA_ERROR, [(127, (109012).to_bytes(4, "big"))])

    await handler.on_package(error)

    assert await handler._ota_queue.get() is error