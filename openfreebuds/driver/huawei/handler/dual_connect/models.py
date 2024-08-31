import json

from openfreebuds.driver.huawei.package import HuaweiSppPackage


class OfbHuaweiDualConnectRow:
    def __init__(self, package: HuaweiSppPackage):
        self.name = package.find_param(9).decode("utf8", "ignore")
        self.auto_connect = package.find_param(8)[0] == 1
        self.preferred = package.find_param(7)[0] == 1
        self.mac = package.find_param(4).hex()

        conn_state = package.find_param(5)[0]
        self.connected = conn_state > 0
        self.playing = conn_state == 9

    def __str__(self):
        return json.dumps({
            "name": self.name,
            "auto_connect": self.auto_connect,
            "preferred": self.preferred,
            "connected": self.connected,
            "playing": self.playing,
        })
