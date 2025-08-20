import json

from openfreebuds.driver.huawei.driver.generic import OfbDriverHandlerHuawei
from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiStateInEarHandler(OfbDriverHandlerHuawei):
    """
    TWS in-ear state detection handler
    """

    handler_id = "tws_in_ear"
    commands = [b'+\x03']

    async def on_init(self):
        await self.driver.put_property("state", "in_ear", "false")

    async def on_package(self, package: HuaweiSppPackage):
        # DEBUG: Log todos os pacotes para encontrar o formato correto do Pro 4
        print(f"[IN-EAR DEBUG] Pacote completo: {package.hex()}")
        
        # Tentar diferentes parâmetros
        for i in range(1, 20):
            for j in range(1, 20):
                try:
                    value = package.find_param(i, j)
                    if len(value) > 0:
                        print(f"[IN-EAR DEBUG] param({i},{j}): {value}")
                except:
                    pass
        
        # Código original
        value = package.find_param(8, 9)
        if len(value) == 1:
            in_ear_state = value[0] == 1
            print(f"[IN-EAR DEBUG] Estado original: {in_ear_state} (raw: {value[0]})")
            await self.driver.put_property("state", "in_ear", json.dumps(in_ear_state))
