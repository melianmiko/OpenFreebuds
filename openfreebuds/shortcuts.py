import openfreebuds_backend
from openfreebuds.constants import OfbEventKind
from openfreebuds.exceptions import OfbAlreadyRunningError, OfbSystemError, OfbNotSupportedError
from openfreebuds.manager.generic import IOpenFreebuds
from openfreebuds.utils.logger import create_logger

log = create_logger("OfbShortcuts")
prop_shortcuts = (
    ("mode_normal", "anc", "mode", "normal"),
    ("mode_cancellation", "anc", "mode", "cancellation"),
    ("mode_awareness", "anc", "mode", "awareness"),
    ("enable_low_latency", "config", "low_latency", "true"),
)


class OfbShortcuts:
    def __init__(self, ofb: IOpenFreebuds):
        self.ofb = ofb

        for name, g, p, v in prop_shortcuts:
            self._add_prop_shortcut(name, g, p, v)

        self.all_handlers: dict[str, tuple[callable, callable]] = {}
        for name in dir(self):
            if name.startswith("do_") and callable(getattr(self, name)):
                action = name.split("do_", 1)[1]
                handler = getattr(self, name)
                validator = getattr(self, f"is_{action}_available", None)
                self.all_handlers[action] = handler, validator

    def _add_prop_shortcut(self, shortcut: str, group: str, prop: str, value: str):
        async def _validate(*_):
            return await self.ofb.get_property(group, prop) is not None

        async def _do(*_):
            await self.ofb.set_property(group, prop, value)

        setattr(self, f"do_{shortcut}", _do)
        setattr(self, f"is_{shortcut}_available", _validate)

    async def execute(self, shortcut, *args, no_catch: bool = False):
        # noinspection PyBroadException
        if shortcut not in self.all_handlers:
            raise OfbNotSupportedError(f"Unknown shortcut {shortcut}")
        handler, validator = self.all_handlers[shortcut]

        try:
            if validator is not None and not await validator():
                log.debug(f"Not supported, skip {shortcut}")
                return

            return await handler(*args)
        except Exception as e:
            if no_catch:
                raise e

    @staticmethod
    def all():
        all_names = [x[0] for x in prop_shortcuts]
        for name in dir(OfbShortcuts):
            if name.startswith("do_") and callable(getattr(OfbShortcuts, name)):
                all_names.append(name.split("do_", 1)[1])
        return sorted(all_names)

    async def do_next_mode(self):
        anc = await self.ofb.get_property("anc")
        if not anc or "mode" not in anc:
            return
        options = list(anc["mode_options"].split(","))
        next_mode = options[(options.index(anc["mode"]) + 1) % len(options)]
        log.info(f"Switch to {next_mode}")
        await self.ofb.set_property("anc", "mode", next_mode)

    async def is_next_mode_available(self):
        return await self.ofb.get_property("anc", "mode") is not None

    async def do_toggle_connect(self):
        _, device_addr = await self.ofb.get_device_tags()
        if await openfreebuds_backend.bt_is_connected(device_addr):
            await self.do_disconnect()
        else:
            await self.do_connect()

    async def do_show_main_window(self):
        await self.ofb.send_message(OfbEventKind.QT_BRING_SETTINGS_UP)

    async def do_refresh_battery(self):
        """Request battery update from device"""
        await self.ofb.request_property_update("battery")

    async def is_refresh_battery_available(self):
        state = await self.ofb.get_state()
        return state == IOpenFreebuds.STATE_CONNECTED

    async def do_disconnect(self):
        state = await self.ofb.get_state()
        if state == IOpenFreebuds.STATE_DISCONNECTED:
            return True
        if state == IOpenFreebuds.STATE_PAUSED:
            raise OfbAlreadyRunningError()

        _, device_addr = await self.ofb.get_device_tags()
        log.info("Trigger device disconnect")
        async with self.ofb.locked_device():
            if not await openfreebuds_backend.bt_disconnect(device_addr):
                raise OfbSystemError()

    async def do_connect(self):
        state = await self.ofb.get_state()
        if state == IOpenFreebuds.STATE_CONNECTED:
            return True
        if state == IOpenFreebuds.STATE_PAUSED:
            raise OfbAlreadyRunningError()

        log.info("Trigger device connect")
        _, device_addr = await self.ofb.get_device_tags()
        # async with self.ofb.locked_device():
        if not await openfreebuds_backend.bt_connect(device_addr):
            raise OfbSystemError()


if __name__ == "__main__":
    # noinspection PyTypeChecker
    print(OfbShortcuts(None).all_handlers)
