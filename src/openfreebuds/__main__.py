import asyncio
import logging

from openfreebuds import create


async def main():
    logging.basicConfig(level=logging.DEBUG)
    openfreebuds = await create()
    print(openfreebuds.role)
    # await asyncio.sleep(1)
    # await openfreebuds.start("HUAWEI FreeBuds 5i" "DC:D4:44:28:6F:AE")
    await asyncio.Event().wait()
    # manager = OpenFreebuds()
    # driver = FbDriverHuawei5i)
    #
    # await manager.start(driver)
    # for i in range(60):
    #     print(manager.state)
    #     await asyncio.sleep(1)
    # # await manager.set_property("anc", "mode", "normal")
    # print(manager._driver._store)


if __name__ == "__main__":
    asyncio.run(main())
