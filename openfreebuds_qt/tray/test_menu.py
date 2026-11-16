from types import SimpleNamespace

import pytest

from openfreebuds.utils.stupid_rpc import RemoteError
from openfreebuds_qt.tray.menu import OfbQtTrayMenu


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
