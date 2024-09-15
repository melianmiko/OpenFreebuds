from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class OfnHuaweiSoundQualityPreferenceHandler(OfbDriverHandlerHuawei):
    """
    Sound quality preference option from 5i, and maybe other devices too
    """
    handler_id = "config_sound_quality"
    commands = [b"\x2b\xa3"]
    ignore_commands = [b"\x2b\xa2"]
    properties = [
        ("sound", "quality_preference"),
    ]

    def __init__(self):
        super().__init__()
        self.options = {
            0: "sqp_connectivity",
            1: "sqp_quality",
        }

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x2b\xa3", [1]))
        await self.on_package(resp)

    async def set_property(self, group: str, prop: str, value):
        value = reverse_dict(self.options)[value]
        pkg = HuaweiSppPackage.change_rq(b"\x2b\xa2", [
            (1, value),
        ])

        await self.driver.send_package(pkg)
        await self.on_init()

    async def on_package(self, package: HuaweiSppPackage):
        value = package.find_param(2)

        if len(value) == 1:
            value = int.from_bytes(value, byteorder="big", signed=True)
            await self.driver.put_property("sound", "quality_preference",
                                           self.options[value])
            await self.driver.put_property("sound", "quality_preference_options",
                                           ",".join(self.options.values()))
