import asyncio

from aiohttp import ClientConnectorError

from openfreebuds.manager.standalone import OpenFreebuds
from openfreebuds.utils.stupid_rpc import test_online, run_rpc_server


async def create():
    """
    Create a new manager instance, or connect to exiting if it's already spawned
    """
    instance = OpenFreebuds()

    try:
        await test_online()
        instance.role = "client"
    except ClientConnectorError:
        instance.server_task = asyncio.create_task(run_rpc_server(instance, ""))

    return instance
