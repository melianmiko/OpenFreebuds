from aiocmd.aiocmd import PromptToolkitCmd

from openfreebuds import IOpenFreebuds


def to_fixed(string, length):
    return string + " " * max(0, length - len(string))


class OpenFreebudsCmd(PromptToolkitCmd):
    manager: IOpenFreebuds = None

    def __init__(self):
        super().__init__(ignore_sigint=False)

    async def do_connect(self, device_name, device_addr):
        await self.manager.start(device_name, device_addr)

    async def do_listen(self):
        print("Listening for incoming events, use Ctrl-C to break...")
        sub_id = await self.manager.subscribe()
        try:
            while True:
                event = await self.manager.wait_for_event(sub_id)
                print(event)
        except KeyboardInterrupt:
            pass
        finally:
            await self.manager.unsubscribe(sub_id)

    async def do_set(self, group, prop, value):
        await self.manager.set_property(group, prop, value)

    async def do_status(self):
        state = await self.manager.get_state()
        print("State:", state)
        if state != IOpenFreebuds.STATE_CONNECTED:
            return

        store = await self.manager.get_property(None, None)
        for group in store:
            print(group)
            for prop in store[group]:
                if prop.endswith("_options") or prop == "supported_languages":
                    print("  ", prop)
                    for opt in store[group][prop].split(","):
                        print("    - ", opt)
                else:
                    print("  ", to_fixed(prop, 30),
                          store[group][prop])
