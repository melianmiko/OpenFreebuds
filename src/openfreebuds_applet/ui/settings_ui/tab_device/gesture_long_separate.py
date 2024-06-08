from openfreebuds_applet.ui.i18n_mappings import GESTURE_ACTION_MAPPINGS
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class LongTapSeparateSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "long_tap_options")
    prop_options_labels = GESTURE_ACTION_MAPPINGS

    prop_primary = ("action", "long_tap_left")
    prop_primary_label = "Long tap on left headphone"

    prop_secondary = ("action", "long_tap_right")
    prop_secondary_label = "Long tap on right headphone"

    category_name = "Long-tap"

    required_props = [
        ("action", "long_tap_left"),
        ("action", "long_tap_options"),
    ]
