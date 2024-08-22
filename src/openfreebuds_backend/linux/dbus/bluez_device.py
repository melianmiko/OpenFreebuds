from sdbus import DbusInterfaceCommonAsync, dbus_property_async, DbusObjectManagerInterfaceAsync, dbus_method_async


class BluezProxy(DbusObjectManagerInterfaceAsync, interface_name="org.bluez"):
    pass


class BluezDevice1Proxy(DbusInterfaceCommonAsync, interface_name="org.bluez.Device1"):
    @dbus_property_async("b")
    def Connected(self) -> bool:
        pass

    @dbus_method_async()
    async def Disconnect(self):
        pass

    @dbus_method_async()
    async def Connect(self):
        pass
