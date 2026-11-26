from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QApplication, QWidget

from openfreebuds import IOpenFreebuds
from openfreebuds.utils.stupid_rpc import RemoteError
from openfreebuds_qt.tray.menu import OfbQtTrayMenu
from openfreebuds_qt.utils.device_errors import spp_port_busy_message


class _FakeConfig:
    def get(self, section, key=None, default=None):
        if section == "ui" and key in ("tray_show_equalizer", "tray_show_dual_connect"):
            return True
        return default

    def set(self, *args):
        pass

    def save(self):
        pass


class _FakeOfb:
    def __init__(self):
        self.name = "A"
        self.props = {}

    async def get_state(self):
        return IOpenFreebuds.STATE_CONNECTED

    async def get_device_tags(self):
        return self.name, f"addr-{self.name}"

    async def get_property(self, group=None, prop=None, fallback=None):
        if group is None:
            return self.props
        if group not in self.props:
            return fallback
        data = self.props[group]
        if prop is None:
            return data
        return data.get(prop, fallback)

    async def get_last_start_error(self):
        return ""

    async def set_property(self, *args):
        return True


def _qapp():
    global _APP
    _APP = QApplication.instance() or QApplication([])
    return _APP


_APP = None


class _FakeAction:
    def __init__(self):
        self.visible = True

    def setVisible(self, value: bool):
        self.visible = value


class _FakeSubmenu:
    def __init__(self):
        self.was_cleared = False

    def clear(self):
        self.was_cleared = True


def test_reset_device_state_hides_cached_device_items():
    section_calls = []
    anc_mode_actions = {"normal": _FakeAction(), "cancellation": _FakeAction()}
    equalizer_action = _FakeAction()
    dual_connect_action = _FakeAction()
    anc_level_action = _FakeAction()
    equalizer_submenu = _FakeSubmenu()
    dual_connect_submenu = _FakeSubmenu()

    fake = SimpleNamespace(
        first_time_render=False,
        battery_section=1,
        anc_section=2,
        anc_mode_actions=anc_mode_actions,
        equalizer_action=equalizer_action,
        dual_connect_action=dual_connect_action,
        anc_level_action=anc_level_action,
        equalizer_submenu=equalizer_submenu,
        dual_connect_submenu=dual_connect_submenu,
        set_section_visible=lambda section, value: section_calls.append((section, value)),
    )

    OfbQtTrayMenu._reset_device_state(fake)

    assert fake.first_time_render is True
    assert section_calls == [(1, False), (2, False)]
    assert equalizer_action.visible is False
    assert dual_connect_action.visible is False
    assert anc_level_action.visible is False
    assert all(not action.visible for action in anc_mode_actions.values())
    assert equalizer_submenu.was_cleared is True
    assert dual_connect_submenu.was_cleared is True


@pytest.mark.asyncio
async def test_remote_dependency_error_opens_dependency_dialog(monkeypatch):
    """RPC wraps the manager exception; the tray must still recognize the missing dependency."""
    calls = []

    class _Dialog:
        def __init__(self, parent, args):
            self.parent = parent
            self.args = args

        async def get_user_response(self):
            calls.append(self.args)

    monkeypatch.setattr("openfreebuds_qt.tray.menu.OfbQtDependencyMissingDialog", _Dialog)

    error = RemoteError({
        "class": "OfbBackendDependencyMissingError",
        "trace": "server trace",
        "args": ["Bluetooth Command Line Tools required", "https://example.invalid/tools.exe"],
    })
    fake = SimpleNamespace(ctx=SimpleNamespace(main_window="main"))

    await OfbQtTrayMenu._handle_shortcut_error(fake, error)

    assert calls == [["Bluetooth Command Line Tools required", "https://example.invalid/tools.exe"]]


@pytest.mark.asyncio
async def test_other_remote_error_opens_error_dialog(monkeypatch):
    """Connect failures other than a missing dependency must be reported, not kill the tray app."""
    calls = []

    class _Dialog:
        def __init__(self, parent):
            self.parent = parent

        async def get_user_response(self, info=""):
            calls.append(info)

    monkeypatch.setattr("openfreebuds_qt.tray.menu.OfbQtErrorDialog", _Dialog)

    error = RemoteError({
        "class": "OfbSystemError",
        "trace": "server trace",
        "args": [],
    })
    fake = SimpleNamespace(ctx=SimpleNamespace(main_window="main"))

    await OfbQtTrayMenu._handle_shortcut_error(fake, error)

    assert calls and "server trace" in calls[0]


@pytest.mark.asyncio
async def test_port_busy_shortcut_error_shows_bluetooth_hint(monkeypatch):
    """A taken RFCOMM endpoint must explain the likely cause in a dedicated notice."""
    calls = []

    async def _show_dialog(parent):
        calls.append(parent)

    monkeypatch.setattr("openfreebuds_qt.tray.menu.show_spp_port_busy_dialog", _show_dialog)

    error = RemoteError({
        "class": "FbStartupError",
        "trace": "server trace",
        "args": ["spp_port_busy"],
    })
    fake = SimpleNamespace(ctx=SimpleNamespace(main_window="main"))

    await OfbQtTrayMenu._handle_shortcut_error(fake, error)

    assert calls == ["main"]
    assert "Bluetooth port" in spp_port_busy_message()


@pytest.mark.asyncio
async def test_failed_state_reports_port_busy_once(monkeypatch):
    """The driver retries every few seconds; the hint must appear once per outage."""
    calls = []

    async def _show_dialog(parent):
        calls.append(parent)

    class _Ofb:
        async def get_last_start_error(self):
            return "spp_port_busy"

    monkeypatch.setattr("openfreebuds_qt.tray.menu.show_spp_port_busy_dialog", _show_dialog)

    fake = SimpleNamespace(
        _start_failure_reported=False,
        ofb=_Ofb(),
        ctx=SimpleNamespace(main_window="main"),
    )

    await OfbQtTrayMenu._report_start_failure(fake, IOpenFreebuds.STATE_FAILED)
    await OfbQtTrayMenu._report_start_failure(fake, IOpenFreebuds.STATE_FAILED)

    assert calls == ["main"]


@pytest.mark.asyncio
async def test_refresh_masks_features_after_silent_device_switch(monkeypatch):
    """The menu must never keep features that the current device lacks.

    A device switch can happen without the tray processing a DEVICE_CHANGED event
    (for example while the event loop is busy). Refreshing right before the menu is
    shown must still rebuild the mask from the manager's current device.
    """
    _qapp()
    monkeypatch.setattr(
        "openfreebuds_qt.tray.menu.OfbQtConfigParser.get_instance",
        classmethod(lambda cls: _FakeConfig()),
    )

    ofb = _FakeOfb()
    menu = OfbQtTrayMenu(None, SimpleNamespace(main_window=QWidget(), ofb=ofb), ofb)

    ofb.props = {
        "anc": {"mode": "normal", "mode_options": "normal,cancellation,awareness",
                "level": "0", "level_options": "0,1,2"},
        "battery": {"global": 50},
        "sound": {"equalizer_preset": "equalizer_preset_default",
                  "equalizer_preset_options": "equalizer_preset_default"},
        "dual_connect": {"preferred_device": "", "devices": "{}"},
    }
    await menu.refresh()

    assert menu.equalizer_action.isVisible()
    assert menu.dual_connect_action.isVisible()
    assert all(action.isVisible() for action in menu.anc_mode_actions.values())

    # Another device is now active, but no event reached the tray.
    ofb.name = "B"
    ofb.props = {}
    await menu.refresh()

    assert not menu.equalizer_action.isVisible()
    assert not menu.dual_connect_action.isVisible()
    assert not menu.anc_level_action.isVisible()
    assert all(not action.isVisible() for action in menu.anc_mode_actions.values())
