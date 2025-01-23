import asyncio
import json

from openfreebuds.constants import APP_ROOT
from openfreebuds.driver.generic import OfbDriverGeneric
from openfreebuds.exceptions import FbStartupError
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbFileDeviceDriver")
files_dir = APP_ROOT / "openfreebuds" / "assets" / "debug_profiles"


class OfbFileDeviceDriver(OfbDriverGeneric):
    def __init__(self, filename: str):
        super().__init__("")
        self._profile_file = filename

    async def start(self):
        path = files_dir / f"{self._profile_file}.json"
        if not path.is_file():
            log.error(f"Profile file not found: {path}")
            raise FbStartupError(f"Profile file not found: {path}")

        with open(path, "r") as f:
            await self.put_property(None, None, json.loads(f.read()))
            log.info(f"Loaded store from {self._profile_file}.json")

        await asyncio.sleep(1)
        self.started = True

    async def stop(self):
        await super().stop()
        self.started = False

    async def set_property(self, group: str, prop: str, value: str):
        log.info(f"SET {group}//{prop} -> {value}")
        return await self.put_property(group, prop, value)

    async def is_device_online(self):
        return True
