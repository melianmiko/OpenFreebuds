from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage


class HuaweiSppHandler:
    handle_commands: list[bytes] = []
    handle_props: list[tuple[str, str]] = []
    ignore_commands: list[bytes] = []
    device = None

    def on_device_ready(self, device):
        self.device = device

    def on_init(self):
        pass

    def on_package(self, package: HuaweiSppPackage):
        raise Exception("Not implemented")

    def on_prop_changed(self, group: str, prop: str, value):
        raise Exception("Not implemented")
