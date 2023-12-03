from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class LongTapSeparateSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "long_tap_options")
    prop_primary = ("action", "long_tap_left")
    prop_secondary = ("action", "long_tap_right")
    category_name = "setup_category_gestures"

    required_props = [
        ("action", "long_tap_left"),
        ("action", "long_tap_options"),
    ]
