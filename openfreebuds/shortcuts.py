import openfreebuds_backend
from openfreebuds.exceptions import FbAlreadyRunningError, FbSystemError, FbNotSupportedError
from openfreebuds.manager.generic import IOpenFreebuds
from openfreebuds.utils.logger import create_logger

log = create_logger("OpenFreebudsShortcuts")


class OpenFreebudsShortcuts:
    def __init__(self, ofb: IOpenFreebuds):
        self.ofb = ofb

    async def execute(self, name, *args):
        # noinspection PyBroadException
        try:
            if name == "disconnect":
                return await self.do_disconnect()
            elif name == "connect":
                return await self.do_connect()
            elif name == "anc_next":
                return await self.do_anc_next()
            elif name == "list_available":
                return await self.list_available()
        except Exception as e:
            log.exception(f"Failed to execute name={name}, args={args}")
            raise e

        raise FbNotSupportedError(f"Unknown shortcut {name}")

    async def list_available(self):
        return [x for x, y in [
            ("connect", True),
            ("disconnect", True),
            ("anc_next", await self.ofb.get_property("anc", "mode") is not None),
        ] if y]

    async def do_anc_next(self):
        anc = await self.ofb.get_property("anc")
        if not anc or "mode" not in anc:
            return
        options = list(anc["mode_options"].split(","))
        next_mode = options[(options.index(anc["mode"]) + 1) % len(options)]
        log.info(f"Switch to {next_mode}")
        await self.ofb.set_property("anc", "mode", next_mode)

    async def do_disconnect(self):
        state = await self.ofb.get_state()
        if state == IOpenFreebuds.STATE_DISCONNECTED:
            return True
        if state == IOpenFreebuds.STATE_PAUSED:
            raise FbAlreadyRunningError()

        _, device_addr = await self.ofb.get_device_tags()
        log.info("Trigger device disconnect")
        async with self.ofb.locked_device():
            if not await openfreebuds_backend.bt_disconnect(device_addr):
                raise FbSystemError()

    async def do_connect(self):
        state = await self.ofb.get_state()
        if state == IOpenFreebuds.STATE_CONNECTED:
            return True
        if state == IOpenFreebuds.STATE_PAUSED:
            raise FbAlreadyRunningError()

        log.info("Trigger device connect")
        _, device_addr = await self.ofb.get_device_tags()
        # async with self.ofb.locked_device():
        if not await openfreebuds_backend.bt_connect(device_addr):
            raise FbSystemError()
