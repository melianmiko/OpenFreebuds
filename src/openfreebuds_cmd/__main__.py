import asyncio

import openfreebuds
from openfreebuds_cmd import OpenFreebudsCmd


async def main():
    manager = await openfreebuds.create()
    OpenFreebudsCmd.manager = manager
    await OpenFreebudsCmd().run()

asyncio.run(main())
