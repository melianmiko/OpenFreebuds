import asyncio

from dbus_next import BusType
from dbus_next.aio import ProxyObject, MessageBus

ALLOWED_PORTALS = [
    "org.freedesktop.impl.portal.desktop.gnome",
]

introspection = """<?xml version="1.0"?>
<!--
 Copyright (C) 2019 Red Hat, Inc

 This library is free software; you can redistribute it and/or
 modify it under the terms of the GNU Lesser General Public
 License as published by the Free Software Foundation; either
 version 2 of the License, or (at your option) any later version.

 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 Lesser General Public License for more details.

 You should have received a copy of the GNU Lesser General Public
 License along with this library. If not, see <http://www.gnu.org/licenses/>.

 Author: Matthias Clasen <mclasen@redhat.com>
-->

<node name="/" xmlns:doc="http://www.freedesktop.org/dbus/1.0/doc.dtd">
  <interface name="org.freedesktop.impl.portal.Background">
    <method name='GetAppState'>
      <arg type="a{sv}" name="apps" direction="out"/>
    </method>
    <method name='NotifyBackground'>
      <arg type="o" name="handle" direction="in"/>
      <arg type="s" name="app_id" direction="in"/>
      <arg type="s" name="name" direction="in"/>
      <arg type="u" name="response" direction="out"/>
      <arg type="a{sv}" name="results" direction="out"/>
    </method>
    <method name='EnableAutostart'>
      <arg type="s" name="app_id" direction="in"/>
      <arg type="b" name="enable" direction="in"/>
      <arg type="as" name="commandline" direction="in"/>
      <arg type="u" name="flags" direction="in"/>
      <arg type="b" name="result" direction="out"/>
    </method>
  </interface>
</node>
"""


class FreedesktopBackgroundPortalProxy:
    def __init__(self, dbus_object: ProxyObject):
        self.dbus_interface = dbus_object.get_interface("org.freedesktop.impl.portal.Background")

    async def enable_autostart(self, app_id: str, command: list[str], value):
        return await self.dbus_interface.call_enable_autostart(app_id, value, command, 0)

    async def is_running(self, app_id):
        return app_id in await self.get_app_state()

    async def get_app_state(self):
        return {k: v.value for k, v in dict(await self.dbus_interface.call_get_app_state()).items()}

    @staticmethod
    async def get():
        bus = await MessageBus(bus_type=BusType.SESSION).connect()

        dbus_introspect = await bus.introspect("org.freedesktop.DBus", "/org/freedesktop/DBus")
        dbus_obj = bus.get_proxy_object("org.freedesktop.DBus", "/org/freedesktop/DBus",
                                        dbus_introspect)
        dbus = dbus_obj.get_interface("org.freedesktop.DBus")

        # noinspection PyUnresolvedReferences
        for name in await dbus.call_list_names():
            if name in ALLOWED_PORTALS:
                obj = bus.get_proxy_object(name, "/org/freedesktop/portal/desktop", introspection)
                return FreedesktopBackgroundPortalProxy(obj)

        return None


if __name__ == "__main__":
    async def main():
        o = await FreedesktopBackgroundPortalProxy.get()
        r = await o.get_app_state()
        print(r)

    asyncio.run(main())
