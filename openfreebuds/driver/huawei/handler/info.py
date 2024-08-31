from contextlib import suppress

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiInfoHandler(OfbDriverHandlerHuawei):
    """
    Device info handler
    """

    handler_id = "device_info"
    commands = [b'\x01\x07']

    descriptor = {
        3: "hardware_ver",
        7: "software_ver",
        9: "serial_number",
        10: "device_submodel",
        15: "device_model"
    }

    async def on_init(self):
        # Try to fetch so much props as we can
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x01\x07", list(range(32))))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        out = {}
        for key in package.parameters:
            if key == 24 and package.parameters[key][0:2] == b"L-":
                # Per-earphone serial numbers
                _parse_per_earphone_sn(out, package.parameters[key].decode("utf8"))
                continue
            out[self.descriptor.get(key, f"field_{key}")] = package.parameters[key].decode("utf8")
        await self.driver.put_property("info", None, out)


def _parse_per_earphone_sn(out, data: str):
    with suppress(Exception):
        left, right = data.split(",")
        out["left_serial_number"] = left[2:]
        out["right_serial_number"] = right[2:]
