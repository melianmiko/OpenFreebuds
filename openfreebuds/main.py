import asyncio
import logging

from aiohttp import ClientConnectorError

from openfreebuds.manager.standalone import OpenFreebuds
from openfreebuds.utils.logger import create_logger
from openfreebuds.utils.stupid_rpc import test_online, run_rpc_server

log = create_logger("OpenFreebudsDaemon")
# await openfreebuds.start("HUAWEI FreeBuds 5i" "DC:D4:44:28:6F:AE")


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


async def main():
    logging.basicConfig(level=logging.DEBUG)
    openfreebuds = await create()
    if openfreebuds.role != "standalone":
        log.error("Can't start: not a primary instance, close all other OpenFreebuds and try again")
        return

    log.info("Ready to accept connections")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        log.info("Gracefully leaving...")
        await openfreebuds.destroy()
