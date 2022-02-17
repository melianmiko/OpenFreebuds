import traceback

import openfreebuds.manager
import openfreebuds.device_names
import logging

# TODO: Long tap settings

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s:%(name)s:%(threadName)s  %(message)s")


def main():
    man = openfreebuds.manager.create()

    print("-- Scan feature test:")
    man.scan(lock=True)
    for i, a in enumerate(man.scan_results):
        print(i, a["name"], "(" + a["address"] + ")", a["connected"])
    print()

    num = int(input("Enter device num to use: "))
    name = man.scan_results[num]["name"]
    address = man.scan_results[num]["address"]

    if not openfreebuds.device_names.is_supported(name):
        print("!! Device with this name isn't tested.")
        print("!! It can work incorrectly with this app")
        if not input("Type yes to continue: ").lower() == "yes":
            print("bye")
            raise SystemExit
    print()

    print("-- Using device", address)
    man.set_device(address)

    while True:
        print("-- Waiting for spp connect...")
        while man.state != man.STATE_CONNECTED:
            man.state_changed.wait()
            man.state_changed.clear()

        shell(man)
        print("-- Device disconnected")


def shell(manager):
    dev = manager.device
    while dev.started:
        cmd = input("openfreebuds> ").split(" ")

        if cmd[0] == "":
            continue

        try:
            if cmd[0] == "l":
                for a in dev.list_properties():
                    print(a, dev.get_property(a))
            elif cmd[0] == "w":
                print("Waiting for spp event...")
                dev.on_event.wait()
                for a in dev.list_properties():
                    print(a, dev.get_property(a))
                dev.on_event.clear()
            elif cmd[0] == "set":
                dev.set_property(cmd[1], int(cmd[2]))
                print("OK")
            elif cmd[0] == "d":
                dev.debug = True
                print("Enabled debug mode")
            elif cmd[0] == "q":
                manager.close()
                print("bye")
                raise SystemExit
            else:
                print("Unknown command")
        except Exception as e:
            # noinspection PyTypeChecker
            traceback.print_exception(e)

        print()


if __name__ == "__main__":
    main()
