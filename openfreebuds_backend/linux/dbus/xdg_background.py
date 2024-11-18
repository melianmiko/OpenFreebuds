import asyncio

from dbus_next import BusType, Variant
from dbus_next.aio import MessageBus, ProxyObject

from openfreebuds_backend.linux.dbus.constants import XDG_DESKTOP_PORTAL_INTROSPECTION
from openfreebuds_backend.linux.dbus.xdg_request import XdgDesktopPortalRequest


class XdgDesktopBackgroundPortal(XdgDesktopPortalRequest):
    @staticmethod
    async def get():
        bus = await MessageBus(bus_type=BusType.SESSION).connect()
        dbus_obj = bus.get_proxy_object("org.freedesktop.portal.Desktop",
                                        "/org/freedesktop/portal/desktop",
                                        XDG_DESKTOP_PORTAL_INTROSPECTION)
        return XdgDesktopBackgroundPortal(dbus_obj)

    def __init__(self, dbus_obj: ProxyObject):
        self._obj = dbus_obj
        self._interface = dbus_obj.get_interface("org.freedesktop.portal.Background")

    async def request_background(self, parent_window: str = "", reason: str = "", autostart: bool = False):
        async with (XdgDesktopPortalRequest().handle_request(self._obj)
                    as (handler_id, expected_path, get_response)):

            # noinspection PyUnresolvedReferences
            actual_path = await self._interface.call_request_background(
                parent_window,
                {
                    "autostart": Variant('b', autostart),
                    "handle_token": Variant('s', handler_id),
                    "reason": Variant('s', reason),
                }
            )

            assert actual_path == expected_path
            code, data = await get_response()

            return code == 0, data["background"].value, data["autostart"].value


async def test():
    bg = await XdgDesktopBackgroundPortal.get()
    ret = await bg.request_background("", "Test", True)
    print(ret)


if __name__ == "__main__":
    asyncio.run(test())
