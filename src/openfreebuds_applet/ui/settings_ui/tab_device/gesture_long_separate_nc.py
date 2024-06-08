from openfreebuds_applet.ui.i18n_mappings import NOISE_CONTROL_OPTION_MAPPING
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class NoiseControlSeparateSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "noise_control_options")
    prop_options_labels = NOISE_CONTROL_OPTION_MAPPING

    prop_primary = ("action", "noise_control_left")
    prop_primary_label = "Preferred modes"

    category_name = "Long-tap"

    required_props = [
        ("action", "noise_control_left"),
        ("action", "noise_control_options"),
    ]
