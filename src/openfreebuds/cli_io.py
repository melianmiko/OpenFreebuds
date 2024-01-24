import logging
import traceback

from openfreebuds.device.generic.base import BaseDevice
from openfreebuds.device.huawei.generic.spp_package import HuaweiSppPackage
from openfreebuds.logger import create_log

log = create_log("CLI-IO")


# noinspection PyBroadException
def dev_command(dev: BaseDevice, cmd: list[str]) -> str:
    out = ""

    try:
        if cmd[0] == "l":
            storage = dev.list_properties()
            for group_name in storage:
                for prop_name in storage[group_name]:
                    out += str(group_name).ljust(10) + " " + str(prop_name).ljust(48) + " " + \
                           str(storage[group_name][prop_name]) + "\n"
        elif cmd[0] == "set":
            dev.set_property(cmd[1], cmd[2], int(cmd[3]))
            out += "OK\n"
        elif cmd[0] == "set_str":
            dev.set_property(cmd[1], cmd[2], cmd[3])
            out += "OK\n"
        elif cmd[0] == "hspp":
            command = bytes.fromhex(cmd[1])
            args = []
            for a in cmd[2:]:
                p_type, p_value = a.split(":")
                args.append((int(p_type), bytes.fromhex(p_value)))
            pkg = HuaweiSppPackage(command, args)
            out += "Send" + str(pkg) + "\n"
            dev.send_package(pkg, True)
        else:
            out += "Unknown device command\n"
    except Exception:
        out += traceback.format_exc()

    log.debug(out)

    return out
