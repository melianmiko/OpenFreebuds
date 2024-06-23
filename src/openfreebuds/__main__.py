import asyncio
import logging

from openfreebuds import create
from openfreebuds.utils.logger import create_logger

log = create_logger("OpenFreebudsDaemon")


# await openfreebuds.start("HUAWEI FreeBuds 5i" "DC:D4:44:28:6F:AE")


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
        log.info("Gracefully closing...")
        await openfreebuds.stop()
        log.info("Bye bye!")


if __name__ == "__main__":
    asyncio.run(main())
