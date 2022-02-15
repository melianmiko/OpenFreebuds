import subprocess

from openfreebuds.manager.base import FreebudsManager

WIN_TOOLS_PATH = "C:\\Program Files (x86)\\Bluetooth Command Line Tools\\bin\\"


class WindowsFreebudsManager(FreebudsManager):
    MAINLOOP_TIMEOUT = 10

    def _is_connected(self):
        command = [WIN_TOOLS_PATH + "btdiscovery.exe",
                   "-b\"(" + self.address + ")\"",
                   "-d\"%c%\""]
        out = str(subprocess.check_output(command))

        return "Yes" in out

    def _device_exists(self):
        # Unavailable in Win32 for now
        return True

    def _do_scan(self):
        command = [WIN_TOOLS_PATH + "btdiscovery.exe", "-d\"%a%;%n%;%r%;%c%\""]
        out = subprocess.check_output(command)
        out = str(out, "utf8").split("\r\n")

        for line in out:
            parts = line[1:-1].split(";")
            if len(parts) > 1 and parts[2] == "Yes":
                self.scan_results.append({
                    "name": parts[1],
                    "address": parts[0],
                    "connected": parts[3] == "Yes"
                })

        self.scan_complete.set()
