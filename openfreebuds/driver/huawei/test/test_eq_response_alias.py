import asyncio
from types import SimpleNamespace

import pytest

from openfreebuds.driver.huawei.driver.generic import OfbDriverHuaweiGeneric, OfbHuaweiResponseReceiver


@pytest.mark.asyncio
async def test_2b4a_notification_completes_pending_2b49_write():
    driver = object.__new__(OfbDriverHuaweiGeneric)
    receiver = OfbHuaweiResponseReceiver()
    setattr(driver, "_OfbDriverHuaweiGeneric__pending_responses", {b"\x2b\x49": receiver})

    pkg = SimpleNamespace(command_id=b"\x2b\x4a")
    driver._resolve_response_alias(pkg)

    assert receiver.is_set()
    assert receiver.package is pkg
