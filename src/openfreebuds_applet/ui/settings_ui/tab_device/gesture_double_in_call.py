from openfreebuds_applet.ui.i18n_mappings import GESTURE_ACTION_MAPPINGS
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class DoubleTapInCallSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "double_tap_in_call_options")
    prop_options_labels = GESTURE_ACTION_MAPPINGS

    prop_primary = ("action", "double_tap_in_call")
    prop_primary_label = "Double-tap in call"
    category_name = "Double-tap"

    required_props = [
        ("action", "double_tap_in_call_options"),
        ("action", "double_tap_in_call"),
    ]
