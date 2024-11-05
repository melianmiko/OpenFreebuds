import asyncio

from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface


class DBusConfigLock:
    task: asyncio.Task
    bus: MessageBus

    @staticmethod
    async def acquire():
        bus = await MessageBus().connect()
        DBusConfigLock.bus = bus

        dbus_introspect = await bus.introspect("org.freedesktop.DBus", "/org/freedesktop/DBus")
        dbus_obj = bus.get_proxy_object("org.freedesktop.DBus", "/org/freedesktop/DBus",
                                        dbus_introspect)
        dbus = dbus_obj.get_interface("org.freedesktop.DBus")

        # noinspection PyUnresolvedReferences
        for name in await dbus.call_list_names():
            if name == "pw.mmk.OpenFreebuds":
                bus.disconnect()
                return False

        # Provide void DBus service
        interface = ServiceInterface('pw.mmk.OpenFreebuds')
        bus.export('/com/example/sample0', interface)
        await bus.request_name('pw.mmk.OpenFreebuds')

        return True
