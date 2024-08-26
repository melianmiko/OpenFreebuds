import asyncio

import openfreebuds
from openfreebuds_cmd.main import OpenFreebudsCmd


def main():
    async def _main():
        manager = await openfreebuds.create()
        OpenFreebudsCmd.manager = manager
        await OpenFreebudsCmd().run()

    return asyncio.run(_main())
