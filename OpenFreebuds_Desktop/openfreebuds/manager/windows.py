import logging
import subprocess
import os

from openfreebuds.manager.base import FreebudsManager

TOOLS_PATH = os.path.dirname(os.path.realpath(__file__)) + "/tools"
log = logging.getLogger("WindowsFreebudsManager")


class WindowsFreebudsManager(FreebudsManager):
    def _is_connected(self):
        command = ["powershell.exe",
                   "-ExecutionPolicy", "RemoteSigned",
                   "-file", TOOLS_PATH + "\\BluetoothDevices.ps1"]

        log.debug("is_connected command=" + str(command))

        out = subprocess.check_output(command)
        out = str(out, "utf8").split("\r\n")

        for line in out:
            parts = line.split(";")
            if parts[1] == self.address:
                result = parts[2] == "True"
                log.debug("is_connected line=" + line + " result=" + str(result))
                return result

        return None

    def _device_exists(self):
        return self._is_connected() is not None

    def _do_scan(self):
        command = ["powershell.exe",
                   "-ExecutionPolicy", "RemoteSigned",
                   "-file", TOOLS_PATH + "\\BluetoothDevices.ps1"]

        log.debug("do_scan command=" + str(command))

        out = subprocess.check_output(command)
        out = str(out, "utf8").split("\r\n")

        for line in out:
            log.debug(line)
            parts = line.split(";")
            if len(parts) > 1:
                self.scan_results.append({
                    "name": parts[0],
                    "address": parts[1],
                    "connected": parts[2] == "True"
                })

        self.scan_complete.set()
