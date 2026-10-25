import pytest

from openfreebuds.driver.huawei.driver.debug import FbDriverHuaweiGenericFixture
from openfreebuds.driver.huawei.handler.state_in_ear import OfbHuaweiStateInEarHandler
from openfreebuds.driver.huawei.package import HuaweiSppPackage


@pytest.mark.asyncio
async def test_per_ear_notifications():
    driver = FbDriverHuaweiGenericFixture([OfbHuaweiStateInEarHandler()], {})
    await driver.start()

    for first, second, expected in [(1, 1, "true"), (0, 1, "false"), (1, 0, "false"), (0, 0, "false"), (1, 1, "true")]:
        package = HuaweiSppPackage(b'+\x25', [(1, first), (2, second)])
        await driver._handle_raw_pkg(package.to_bytes())
        assert await driver.get_property("state", "in_ear") == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("param", [8, 9])
async def test_legacy_notifications(param):
    driver = FbDriverHuaweiGenericFixture([OfbHuaweiStateInEarHandler()], {})
    await driver.start()

    for value, expected in [(1, "true"), (0, "false")]:
        package = HuaweiSppPackage(b'+\x03', [(param, value)])
        await driver._handle_raw_pkg(package.to_bytes())
        assert await driver.get_property("state", "in_ear") == expected
