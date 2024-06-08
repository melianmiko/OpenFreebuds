from openfreebuds_applet.ui.i18n_mappings import GESTURE_ACTION_MAPPINGS
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class DoubleTapSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "double_tap_options")
    prop_options_labels = GESTURE_ACTION_MAPPINGS

    prop_primary = ("action", "double_tap_left")
    prop_primary_label = "Double-tap on left"

    prop_secondary = ("action", "double_tap_right")
    prop_secondary_label = "Double-tap on right"

    category_name = "Double-tap"

    required_props = [
        ("action", "double_tap_options"),
        ("action", "double_tap_left"),
    ]
