import asyncio
import json
import logging

from aiohttp import ClientConnectorError

from openfreebuds.constants import STORAGE_PATH
from openfreebuds.manager.main import OfbManager
from openfreebuds.utils.logger import create_logger
from openfreebuds.utils.stupid_rpc import test_online, run_rpc_server

log = create_logger("OpenFreebudsDaemon")


async def create(kwargs: dict = None):
    """
    Create a new manager instance, or connect to exiting if it's already spawned
    """
    instance = OfbManager()

    if kwargs is None:
        # noinspection PyBroadException
        try:
            rpc_config_path = STORAGE_PATH / "openfreebuds_rpc.json"
            log.info(f"Will load RPC config from {rpc_config_path}")
            with open(rpc_config_path, "r") as f:
                kwargs = json.load(f)
        except Exception:
            kwargs = {}

    instance.rpc_config = kwargs

    try:
        await test_online()
        instance.role = "client"
    except ClientConnectorError:
        instance.server_task = asyncio.create_task(run_rpc_server(instance, **kwargs))

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
