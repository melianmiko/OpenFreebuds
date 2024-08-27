from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class FbHuaweiInfoHandler(FbDriverHandlerHuawei):
    """
    Device info handler
    """

    handler_id = "device_info"
    commands = [b'\x01\x07']

    descriptor = {
        3: "device_ver",
        7: "software_ver",
        9: "serial_number",
        10: "device_model",
        15: "ota_version"
    }

    async def on_init(self):
        # Try to fetch so much props as we can
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x01\x07", list(range(32))))
        await self.on_package(resp)

    async def on_package(self, package: HuaweiSppPackage):
        out = {}
        for key in package.parameters:
            out[self.descriptor.get(key, f"field_{key}")] = package.parameters[key].decode("utf8")
        await self.driver.put_property("info", None, out)
