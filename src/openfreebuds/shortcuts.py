import openfreebuds_backend
from openfreebuds.exceptions import FbAlreadyRunningError, FbSystemError, FbNotSupportedError
from openfreebuds.manager.generic import IOpenFreebuds


class OpenFreebudsShortcuts:
    def __init__(self, ofb: IOpenFreebuds):
        self.ofb = ofb

    async def execute(self, name, *args):
        if name == "disconnect":
            return await self.do_disconnect()
        elif name == "connect":
            return await self.do_connect()

        raise FbNotSupportedError(f"Unknown shortcut {name}")

    async def do_disconnect(self):
        state = await self.ofb.get_state()
        if state == IOpenFreebuds.STATE_DISCONNECTED:
            return True
        if state == IOpenFreebuds.STATE_PAUSED:
            raise FbAlreadyRunningError()

        _, device_addr = await self.ofb.get_device_tags()
        async with self.ofb.locked_device():
            if not await openfreebuds_backend.bt_disconnect(device_addr):
                raise FbSystemError()

    async def do_connect(self):
        state = await self.ofb.get_state()
        if state == IOpenFreebuds.STATE_CONNECTED:
            return True
        if state == IOpenFreebuds.STATE_PAUSED:
            raise FbAlreadyRunningError()

        _, device_addr = await self.ofb.get_device_tags()
        async with self.ofb.locked_device():
            if not await openfreebuds_backend.bt_connect(device_addr):
                raise FbSystemError()
