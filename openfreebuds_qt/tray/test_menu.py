from types import SimpleNamespace

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
