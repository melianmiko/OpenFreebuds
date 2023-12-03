from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class LongTapSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "long_tap_options")
    prop_primary = ("action", "long_tap")
    prop_primary_label = "long_tap_left"
    category_name = "setup_category_gestures"

    required_props = [
        ("action", "long_tap"),
        ("action", "long_tap_options"),
    ]
