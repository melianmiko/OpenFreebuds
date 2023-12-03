from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class PowerButtonSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "power_button_options")
    prop_primary = ("action", "power_button")
    prop_primary_label = "conf_action_power_button"
    category_name = "setup_category_gestures"

    required_props = [
        ("action", "power_button"),
        ("action", "power_button_options"),
    ]
