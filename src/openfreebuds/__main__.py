import asyncio
import logging

from openfreebuds.driver.huawei.generic import FbDriverHuaweiGeneric
from openfreebuds.driver.huawei.handler.anc import FbHuaweiAncHandler
from openfreebuds.main import OpenFreebuds


async def main():
    logging.basicConfig(level=logging.DEBUG)
    manager = OpenFreebuds()
    driver = FbDriverHuaweiGeneric("DC:D4:44:28:6F:AE")
    driver.handlers = [
        FbHuaweiAncHandler(w_cancel_lvl=True, w_cancel_dynamic=True),
    ]

    await manager.start(driver)
    print("manager ready")
    await asyncio.sleep(10)
    await manager.set_property("anc", "mode", "normal")
    print(manager._driver._store)


if __name__ == "__main__":
    asyncio.run(main())
