import logging
import traceback

log = logging.getLogger("CLI-IO")


# noinspection PyBroadException
def dev_command(manager, cmd: list[str]) -> str:
    dev = manager.device
    out = ""

    try:
        if cmd[0] == "l":
            for a in dev.list_properties():
                out += str(a) + " " + str(dev.get_property(a)) + "\n"
        elif cmd[0] == "set":
            dev.set_property(cmd[1], int(cmd[2]))
            out += "OK\n"
        elif cmd[0] == "set_str":
            dev.set_property(cmd[1], cmd[2])
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
