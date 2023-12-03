from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class NoiseControlSeparateSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "noise_control_options")
    prop_primary = ("action", "noise_control_left")
    category_name = "setup_category_gestures"

    required_props = [
        ("action", "noise_control_left"),
        ("action", "noise_control_options"),
    ]
