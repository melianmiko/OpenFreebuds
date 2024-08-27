from openfreebuds.driver.huawei.generic import FbDriverHuaweiGeneric
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class FbDriverHuaweiGenericLoggable(FbDriverHuaweiGeneric):
    def __init__(self, address):
        super().__init__(address)
        self.package_log: list[tuple[str, bytes]] = []

    async def _handle_raw_pkg(self, pkg):
        await super()._handle_raw_pkg(pkg)
        self.package_log.append(("recv", pkg))

    async def _send_nowait(self, pkg: HuaweiSppPackage):
        await super()._send_nowait(pkg)
        self.package_log.append(("send", pkg.to_bytes()))


class FbDriverHuaweiGenericFixture(FbDriverHuaweiGenericLoggable):
    def __init__(self, handlers, package_response_model):
        super().__init__("")
        self.handlers = handlers
        self.package_response_model: dict[bytes, list[bytes]] = package_response_model

    async def start(self):
        await self._start_all_handlers()
        self.package_log = []

    async def stop(self):
        pass

    async def _send_nowait(self, pkg: HuaweiSppPackage):
        rx = pkg.to_bytes()
        self.package_log.append(("send", rx))

        if rx in self.package_response_model:
            responses = self.package_response_model[rx]
            for tx in responses:
                await self._handle_raw_pkg(tx)
