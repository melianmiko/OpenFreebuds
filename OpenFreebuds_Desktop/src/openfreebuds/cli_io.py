import logging
import traceback

from openfreebuds.device.base import BaseDevice

log = logging.getLogger("CLI-IO")


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
        elif cmd[0] == "w":
            ints = []
            for a in cmd[1:]:
                ints.append(int(a))
            out += "Wrote command: " + str(ints) + "\n"
            dev.send_command(ints, True)
        else:
            out += "Unknown device command\n"
    except Exception:
        out += traceback.format_exc()

    log.debug(out)

    return out
