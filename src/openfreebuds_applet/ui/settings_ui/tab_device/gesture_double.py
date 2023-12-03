from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class DoubleTapSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "double_tap_options")
    prop_primary = ("action", "double_tap_left")
    prop_secondary = ("action", "double_tap_right")
    category_name = "setup_category_gestures"

    required_props = [
        ("action", "double_tap_options"),
        ("action", "double_tap_left"),
    ]
