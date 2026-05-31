import pytest

from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import HuaweiFeatureSwitchSpec, OfbHuaweiFeatureSwitchHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


HUAWEI_UNSUPPORTED_ERROR = b"\x00\x01\x86\xa3"


@pytest.mark.asyncio
async def test_feature_switch_query_and_set():
    get_smart_charge_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 4), (2, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_smart_charge_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 4), (2, 1)],
    ).to_bytes()
    set_smart_charge_off_rq = HuaweiSppPackage.change_rq(
        b"\x2b\xb4",
        [(1, 4), (2, 0)],
    ).to_bytes()
    set_smart_charge_off_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 4), (2, 0)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({"smart_charge": 4}),
        ],
        package_response_model={
            get_smart_charge_rq: [get_smart_charge_resp],
            set_smart_charge_off_rq: [set_smart_charge_off_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("features", "smart_charge") == "true"

    await driver.set_property("features", "smart_charge", "false")

    assert await driver.get_property("features", "smart_charge") == "false"


@pytest.mark.asyncio
async def test_feature_switch_ignores_unknown_feature_id():
    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({"smart_charge": 4}),
        ],
        package_response_model={
            HuaweiSppPackage(
                b"\x2b\xb4",
                [(1, 4), (2, b"")],
                resp=b"\x2b\xb4",
            ).to_bytes(): [
                HuaweiSppPackage(
                    b"\x2b\xb4",
                    [(1, 99), (2, 1)],
                ).to_bytes()
            ],
        },
    )

    await driver.start()

    assert await driver.get_property("features", "smart_charge") is None


@pytest.mark.asyncio
async def test_feature_switch_can_write_extended_state_payload():
    get_voice_control_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 35), (2, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_voice_control_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 35), (2, b"\x00\x00\x00\x00")],
    ).to_bytes()
    set_voice_control_on_rq = HuaweiSppPackage.change_rq(
        b"\x2b\xb4",
        [(1, 35), (2, b"\x01\x00\x00\x00")],
    ).to_bytes()
    set_voice_control_on_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 35), (2, b"\x01\x00\x00\x00")],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({"voice_control": HuaweiFeatureSwitchSpec(35, write_payload_size=4)}),
        ],
        package_response_model={
            get_voice_control_rq: [get_voice_control_resp],
            set_voice_control_on_rq: [set_voice_control_on_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("features", "voice_control") == "false"

    await driver.set_property("features", "voice_control", "true")

    assert await driver.get_property("features", "voice_control") == "true"
    assert driver.package_log[0] == ("send", set_voice_control_on_rq)


@pytest.mark.asyncio
async def test_feature_switch_can_read_state_from_alternate_param():
    get_voice_wakeup_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 3), (2, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_voice_wakeup_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 3), (2, b"\x00\x00"), (3, 1)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({"voice_wakeup": HuaweiFeatureSwitchSpec(3, state_param=3)}),
        ],
        package_response_model={
            get_voice_wakeup_rq: [get_voice_wakeup_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("features", "voice_wakeup") == "true"


@pytest.mark.asyncio
async def test_feature_switch_can_read_without_state_query_param():
    get_head_control_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 11)],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_head_control_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 11), (2, 1), (3, 2), (4, 1)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({"head_control": HuaweiFeatureSwitchSpec(11, read_params=())}),
        ],
        package_response_model={
            get_head_control_rq: [get_head_control_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("features", "head_control") == "true"


@pytest.mark.asyncio
async def test_feature_switch_can_store_option_values_in_custom_group():
    get_earplug_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 8), (2, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_earplug_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 8), (2, 2)],
    ).to_bytes()
    set_earplug_rq = HuaweiSppPackage.change_rq(
        b"\x2b\xb4",
        [(1, 8), (2, 3)],
    ).to_bytes()
    set_earplug_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 8), (2, 3)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({
                "earplug_type": HuaweiFeatureSwitchSpec(
                    8,
                    group="config",
                    options={0: "type_0", 1: "type_1", 2: "type_2", 3: "type_3"},
                ),
            }),
        ],
        package_response_model={
            get_earplug_rq: [get_earplug_resp],
            set_earplug_rq: [set_earplug_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("config", "earplug_type") == "type_2"

    await driver.set_property("config", "earplug_type", "type_3")

    assert await driver.get_property("config", "earplug_type") == "type_3"
    assert driver.package_log[0] == ("send", set_earplug_rq)


@pytest.mark.asyncio
async def test_feature_switch_can_parse_multiple_properties_from_same_feature():
    get_spatial_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 24), (2, b""), (3, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_spatial_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 24), (2, 1), (3, 2)],
    ).to_bytes()
    set_room_rq = HuaweiSppPackage.change_rq(
        b"\x2b\xb4",
        [(1, 24), (3, 3)],
    ).to_bytes()
    set_room_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 24), (2, 1), (3, 3)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({
                "spatial_audio_mode": HuaweiFeatureSwitchSpec(
                    24,
                    group="sound",
                    read_params=(2, 3),
                    options={0: "off", 1: "head_tracking", 2: "fixed"},
                ),
                "spatial_audio_room": HuaweiFeatureSwitchSpec(
                    24,
                    group="sound",
                    read_params=(2, 3),
                    state_param=3,
                    options={0: "default", 1: "listen_book", 2: "cinema", 3: "music_hall"},
                ),
            }),
        ],
        package_response_model={
            get_spatial_rq: [get_spatial_resp],
            set_room_rq: [set_room_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("sound", "spatial_audio_mode") == "head_tracking"
    assert await driver.get_property("sound", "spatial_audio_room") == "cinema"

    await driver.set_property("sound", "spatial_audio_room", "music_hall")

    assert await driver.get_property("sound", "spatial_audio_room") == "music_hall"
    assert driver.package_log[0] == ("send", set_room_rq)


@pytest.mark.asyncio
async def test_feature_switch_waits_for_matching_feature_id_response():
    get_spatial_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 24), (2, b""), (3, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    unrelated_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 5), (2, 1)],
    ).to_bytes()
    get_spatial_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 24), (2, 2), (3, 0)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({
                "spatial_audio_mode": HuaweiFeatureSwitchSpec(
                    24,
                    group="sound",
                    read_params=(2, 3),
                    options={0: "off", 1: "head_tracking", 2: "fixed"},
                ),
            }),
        ],
        package_response_model={
            get_spatial_rq: [unrelated_resp, get_spatial_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("sound", "spatial_audio_mode") == "fixed"


@pytest.mark.asyncio
async def test_feature_switch_hides_when_device_returns_error():
    get_smart_charge_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 4), (2, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_smart_charge_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(127, HUAWEI_UNSUPPORTED_ERROR)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({"smart_charge": 4}),
        ],
        package_response_model={get_smart_charge_rq: [get_smart_charge_resp]},
    )

    await driver.start()

    assert await driver.get_property("features", "smart_charge") is None


@pytest.mark.asyncio
async def test_feature_switch_does_not_fake_state_on_write_error():
    get_smart_charge_rq = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 4), (2, b"")],
        resp=b"\x2b\xb4",
    ).to_bytes()
    get_smart_charge_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(1, 4), (2, 0)],
    ).to_bytes()
    set_smart_charge_on_rq = HuaweiSppPackage.change_rq(
        b"\x2b\xb4",
        [(1, 4), (2, 1)],
    ).to_bytes()
    set_smart_charge_on_resp = HuaweiSppPackage(
        b"\x2b\xb4",
        [(127, HUAWEI_UNSUPPORTED_ERROR)],
    ).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[
            OfbHuaweiFeatureSwitchHandler({"smart_charge": 4}),
        ],
        package_response_model={
            get_smart_charge_rq: [get_smart_charge_resp],
            set_smart_charge_on_rq: [set_smart_charge_on_resp],
        },
    )

    await driver.start()

    await driver.set_property("features", "smart_charge", "true")

    assert await driver.get_property("features", "smart_charge") == "false"