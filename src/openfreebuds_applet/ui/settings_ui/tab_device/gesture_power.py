from openfreebuds_applet.ui.i18n_mappings import GESTURE_ACTION_MAPPINGS
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class PowerButtonSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "power_button_options")
    prop_options_labels = GESTURE_ACTION_MAPPINGS

    prop_primary = ("action", "power_button")
    prop_primary_label = "Power button action"
    category_name = "Other gestures"

    required_props = [
        ("action", "power_button"),
        ("action", "power_button_options"),
    ]
