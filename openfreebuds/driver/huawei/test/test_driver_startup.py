import asyncio

import pytest

from openfreebuds.driver.generic.spp import OfbDriverSppGeneric
from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei, OfbDriverHuaweiGeneric


class SlowInitHandler(OfbDriverHandlerHuawei):
    handler_id = "slow_init"
    properties = [("config", "slow_init")]

    def __init__(self):
        self.init_started = asyncio.Event()
        self.release_init = asyncio.Event()

    async def on_init(self):
        self.init_started.set()
        await self.release_init.wait()


@pytest.mark.asyncio
async def test_huawei_driver_start_does_not_wait_for_handler_init(monkeypatch):
    async def fake_spp_start(self):
        self.started = True

    async def fake_spp_stop(self):
        self.started = False

    monkeypatch.setattr(OfbDriverSppGeneric, "start", fake_spp_start)
    monkeypatch.setattr(OfbDriverSppGeneric, "stop", fake_spp_stop)

    driver = OfbDriverHuaweiGeneric("")
    handler = SlowInitHandler()
    driver.handlers = [handler]

    await asyncio.wait_for(driver.start(), timeout=0.2)
    await asyncio.wait_for(handler.init_started.wait(), timeout=0.2)

    report = await driver.get_health_report()
    assert driver.started is True
    assert handler.driver is driver
    assert report["handlers_init_task_alive"] is True
    assert "config//slow_init" in report["available_store_handlers"]

    await driver.stop()

    report = await driver.get_health_report()
    assert driver.started is False
    assert report["handlers_init_task_alive"] is False
