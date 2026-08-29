import pytest

from openfreebuds.driver.huawei.constants import (
    CMD_LEFT_RIGHT_EAR_RECOGNITION_READ,
    CMD_LEFT_RIGHT_EAR_RECOGNITION_WRITE,
)
from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler import OfbHuaweiLeftRightEarRecognitionHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


HUAWEI_UNSUPPORTED_ERROR = b"\x00\x01\x86\xa3"


@pytest.mark.asyncio
async def test_left_right_ear_recognition_query_and_set():
    get_rq = HuaweiSppPackage(
        CMD_LEFT_RIGHT_EAR_RECOGNITION_READ,
        [(1, b"")],
        resp=CMD_LEFT_RIGHT_EAR_RECOGNITION_READ,
    ).to_bytes()
    get_resp = HuaweiSppPackage(CMD_LEFT_RIGHT_EAR_RECOGNITION_READ, [(1, 1)]).to_bytes()
    set_off_rq = HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_EAR_RECOGNITION_WRITE, [(1, 0)]).to_bytes()
    set_off_resp = HuaweiSppPackage(CMD_LEFT_RIGHT_EAR_RECOGNITION_WRITE, [(1, 0)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiLeftRightEarRecognitionHandler()],
        package_response_model={
            get_rq: [get_resp],
            set_off_rq: [set_off_resp],
        },
    )

    await driver.start()

    assert await driver.get_property("features", "left_right_ear_recognition") == "true"

    await driver.set_property("features", "left_right_ear_recognition", "false")

    assert await driver.get_property("features", "left_right_ear_recognition") == "false"
    assert driver.package_log[0] == ("send", set_off_rq)


@pytest.mark.asyncio
async def test_left_right_ear_recognition_hides_when_device_returns_error():
    get_rq = HuaweiSppPackage(
        CMD_LEFT_RIGHT_EAR_RECOGNITION_READ,
        [(1, b"")],
        resp=CMD_LEFT_RIGHT_EAR_RECOGNITION_READ,
    ).to_bytes()
    get_resp = HuaweiSppPackage(CMD_LEFT_RIGHT_EAR_RECOGNITION_READ, [(127, HUAWEI_UNSUPPORTED_ERROR)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiLeftRightEarRecognitionHandler()],
        package_response_model={get_rq: [get_resp]},
    )

    await driver.start()

    assert await driver.get_property("features", "left_right_ear_recognition") is None

    await driver.set_property("features", "left_right_ear_recognition", "true")

    assert await driver.get_property("features", "left_right_ear_recognition") is None
    assert driver.package_log == []


@pytest.mark.asyncio
async def test_left_right_ear_recognition_does_not_fake_state_on_write_error():
    get_rq = HuaweiSppPackage(
        CMD_LEFT_RIGHT_EAR_RECOGNITION_READ,
        [(1, b"")],
        resp=CMD_LEFT_RIGHT_EAR_RECOGNITION_READ,
    ).to_bytes()
    get_resp = HuaweiSppPackage(CMD_LEFT_RIGHT_EAR_RECOGNITION_READ, [(1, 1)]).to_bytes()
    set_off_rq = HuaweiSppPackage.change_rq(CMD_LEFT_RIGHT_EAR_RECOGNITION_WRITE, [(1, 0)]).to_bytes()
    set_off_resp = HuaweiSppPackage(CMD_LEFT_RIGHT_EAR_RECOGNITION_WRITE, [(127, HUAWEI_UNSUPPORTED_ERROR)]).to_bytes()

    driver = FbDriverHuaweiGenericFixture(
        handlers=[OfbHuaweiLeftRightEarRecognitionHandler()],
        package_response_model={
            get_rq: [get_resp],
            set_off_rq: [set_off_resp],
        },
    )

    await driver.start()

    await driver.set_property("features", "left_right_ear_recognition", "false")

    assert await driver.get_property("features", "left_right_ear_recognition") == "true"