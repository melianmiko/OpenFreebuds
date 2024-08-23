from openfreebuds.driver.huawei.generic import FbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage
from openfreebuds.utils import reverse_dict


class FbHuaweiAncLegacyChangeHandler(FbDriverHandlerHuawei):
    """
    This handler wait for 2b03 command package to
    detect ANC mode change via on-device button
    """
    handler_id = "anc_change"
    commands = [b"\x2b\x03"]

    async def on_package(self, package: HuaweiSppPackage):
        data = package.find_param(1)
        if len(data) == 1 and 0 <= data[0] <= 2:
            await self.driver.send_package(HuaweiSppPackage(b"\x2b\x2a", [
                (1, b""),
            ]))


class FbHuaweiAncHandler(FbDriverHandlerHuawei):
    """
    ANC mode switching handler.
    """

    handler_id = "anc_global"
    properties = [
        ('anc', 'mode'),
        ('anc', 'level'),
    ]
    commands = [b"\x2b\x2a"]
    ignore_commands = [b"\x2b\x04"]

    def __init__(self, w_cancel_lvl=False, w_cancel_dynamic=False, w_voice_boost=False):
        self.w_cancel_lvl = w_cancel_lvl
        self.w_voice_boost = w_voice_boost
        self.active_mode = 0

        self.mode_options = {
            0: "normal",
            1: "cancellation",
            2: "awareness",
        }
        self.cancel_level_options = {
            1: "comfort",
            0: "normal",
            2: "ultra",
        }
        self.awareness_level_options = {
            1: "voice_boost",
            2: "normal",
        }

        if w_cancel_dynamic:
            self.cancel_level_options[3] = "dynamic"

    async def on_init(self):
        resp = await self.driver.send_package(HuaweiSppPackage.read_rq(b"\x2b\x2a", [1, 2]))
        await self.on_package(resp)

    async def on_package(self, pkg: HuaweiSppPackage):
        data = pkg.find_param(1)

        if len(data) == 2:
            self.active_mode = data[1]
            new_props = {
                "mode": self.mode_options.get(data[1], data[1]),
                "mode_options": ",".join(self.mode_options.values()),
            }

            if data[1] == 1 and self.w_cancel_lvl:
                # If cancellation turned on and support levels, list them
                new_props["level"] = self.cancel_level_options.get(data[0], data[0])
                new_props["level_options"] = ",".join(self.cancel_level_options.values())

            if data[1] == 2 and self.w_voice_boost:
                # If awareness turned on and support voice boost
                new_props["level"] = "voice_boost" if data[0] != 0 else "normal"
                new_props["level_options"] = "normal,voice_boost"

            await self.driver.put_property("anc", None, new_props)

    async def set_property(self, group: str, prop: str, value):
        if prop == "mode":
            options = self.mode_options
        elif self.active_mode != 2:
            options = self.cancel_level_options
        else:
            options = self.awareness_level_options

        value_byte = reverse_dict(options)[value]
        value_byte = int(value_byte).to_bytes(1, byteorder="big")

        if prop == "mode":
            # Change mode
            data = value_byte + (b"\x00" if value_byte == 0 else b"\xff")
        else:
            # Just change level
            active_mode_value = int(self.active_mode).to_bytes(1, byteorder="big")
            data = active_mode_value + value_byte

        pkg = HuaweiSppPackage.change_rq(cmd=b"\x2b\x04",
                                         parameters=[
                                             (1, data)
                                         ])

        await self.driver.send_package(pkg)
        await self.on_init()
