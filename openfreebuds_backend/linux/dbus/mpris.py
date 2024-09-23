import asyncio

from dbus_next import BusType
from dbus_next.aio import MessageBus, ProxyObject


class MPRISPProxy:
    def __init__(self, dbus_object: ProxyObject):
        super().__init__()
        self.dbus_interface_base = dbus_object.get_interface("org.mpris.MediaPlayer2")
        self.dbus_interface_player = dbus_object.get_interface("org.mpris.MediaPlayer2.Player")

    @staticmethod
    async def get_all():
        items: list[MPRISPProxy] = []
        bus = await MessageBus(bus_type=BusType.SESSION).connect()

        dbus_introspect = await bus.introspect("org.freedesktop.DBus", "/org/freedesktop/DBus")
        dbus_obj = bus.get_proxy_object("org.freedesktop.DBus", "/org/freedesktop/DBus",
                                        dbus_introspect)
        dbus = dbus_obj.get_interface("org.freedesktop.DBus")

        # noinspection PyUnresolvedReferences
        for name in await dbus.call_list_names():
            if name.startswith("org.mpris.MediaPlayer2"):
                introspect = await bus.introspect(name, "/org/mpris/MediaPlayer2")
                obj = bus.get_proxy_object(name, "/org/mpris/MediaPlayer2", introspect)
                items.append(MPRISPProxy(obj))
        return items

    async def pause(self):
        # noinspection PyUnresolvedReferences
        return await self.dbus_interface_player.call_pause()

    async def play(self):
        # noinspection PyUnresolvedReferences
        return await self.dbus_interface_player.call_play()

    async def identity(self) -> str:
        # noinspection PyUnresolvedReferences
        return await self.dbus_interface_base.get_identity()

    async def playback_status(self) -> str:
        # noinspection PyUnresolvedReferences
        return await self.dbus_interface_player.get_playback_status()


if __name__ == "__main__":
    async def main():
        for obj in await MPRISPProxy.get_all():
            print(await obj.playback_status())

    asyncio.run(main())
