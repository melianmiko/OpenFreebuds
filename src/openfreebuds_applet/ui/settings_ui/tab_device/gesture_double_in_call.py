from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class DoubleTapInCallSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "double_tap_in_call_options")
    prop_primary = ("action", "double_tap_in_call")
    category_name = "category_double_tap"

    required_props = [
        ("action", "double_tap_in_call_options"),
        ("action", "double_tap_in_call"),
    ]
