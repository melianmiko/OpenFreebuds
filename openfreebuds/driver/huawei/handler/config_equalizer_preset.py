from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class FbHuaweiEqualizerPresetHandler(FbDriverHandlerHuawei):
    """
    Built-in equalizer settings handler (5i)
    """
    handler_id = "config_eq"
    properties = [
        ("config", "equalizer_preset")
    ]
    commands = [b"\x2b\x4a"]
    ignore_commands = [b"\x2b\x49"]

    def __init__(self, w_presets=None):
        self.w_presets = w_presets or {}
        for i in self.w_presets:
            self.w_presets[i] = "equalizer_preset_" + self.w_presets[i]

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x2b\x4a", [2]))
        await self.on_package(resp)

    async def set_property(self, group: str, prop: str, value):
        value = reverse_dict(self.w_presets)[value]
        pkg = HuaweiSppPackage.change_rq(b"\x2b\x49", [
            (1, value),
        ])
        await self.driver.send_package(pkg)
        await self.on_init()

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(2)

        if len(value) == 1:
            value = int.from_bytes(value, byteorder="big", signed=True)
            await self.driver.put_property("config", "equalizer_preset",
                                     self.w_presets.get(value, f"unknown_{value}"))
            await self.driver.put_property("config", "equalizer_preset_options",
                                     ",".join(self.w_presets.values()))
