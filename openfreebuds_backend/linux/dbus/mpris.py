from sdbus import DbusInterfaceCommonAsync, dbus_property_async, dbus_method_async
from sdbus_async.dbus_daemon import FreedesktopDbus


class MPRISPProxy(DbusInterfaceCommonAsync, interface_name="org.mpris.MediaPlayer2"):
    def __init__(self, service_name):
        super().__init__()
        self._proxify(service_name, "/org/mpris/MediaPlayer2")
        self.Player = MPRISPlayer2Proxy.new_proxy(service_name, "/org/mpris/MediaPlayer2")

    @staticmethod
    async def get_all():
        items: list[MPRISPProxy] = []
        bus = FreedesktopDbus()
        for name in await bus.list_names():
            if name.startswith("org.mpris.MediaPlayer2"):
                items.append(MPRISPProxy(name))
        return items

    @dbus_property_async("s")
    def Identity(self) -> str:
        pass


class MPRISPlayer2Proxy(DbusInterfaceCommonAsync, interface_name="org.mpris.MediaPlayer2.Player"):
    @dbus_property_async("s")
    def PlaybackStatus(self) -> str:
        pass

    @dbus_method_async()
    async def Pause(self):
        pass

    @dbus_method_async()
    async def Play(self):
        pass
