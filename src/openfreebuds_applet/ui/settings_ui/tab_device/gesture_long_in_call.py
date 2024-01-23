from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class LongTapInCallSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "long_tap_in_call_options")
    prop_primary = ("action", "long_tap_in_call")
    category_name = "setup_category_gestures"

    required_props = [
        ("action", "long_tap_in_call"),
        ("action", "long_tap_in_call_options"),
    ]
