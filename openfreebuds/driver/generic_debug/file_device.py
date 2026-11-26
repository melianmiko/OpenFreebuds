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
        result = await self.put_property(group, prop, value)

        # Keep the ringing state in sync so the find-earbud buttons behave like a real device
        if group == "config" and prop == "find_earbud" and isinstance(value, str):
            await self._emulate_find_earbud(value)

        return result

    async def _emulate_find_earbud(self, value: str):
        verb, _, side = value.strip().lower().partition(":")
        side = side or "both"
        target = {
            "left": {"left"},
            "right": {"right"},
            "both": {"left", "right"},
        }.get(side)
        if target is None:
            return

        current = await self.get_property("state", "find_earbud_ringing") or ""
        ringing = {part for part in current.split(",") if part}
        if verb == "ring":
            ringing |= target
        elif verb == "stop":
            ringing -= target
        else:
            return

        await self.put_property("state", "find_earbud_ringing", ",".join(sorted(ringing)))

    async def is_device_online(self):
        return True
