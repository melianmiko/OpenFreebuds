from openfreebuds_applet.ui.i18n_mappings import GESTURE_ACTION_MAPPINGS
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class LongTapSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "long_tap_options")
    prop_options_labels = GESTURE_ACTION_MAPPINGS

    prop_primary = ("action", "long_tap")
    prop_primary_label = "Long tap on left headphone"
    category_name = "Long-tap"

    required_props = [
        ("action", "long_tap"),
        ("action", "long_tap_options"),
    ]
