from openfreebuds_applet.ui.i18n_mappings import GESTURE_ACTION_MAPPINGS
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class SwipeGestureSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "swipe_gesture_options")
    prop_options_labels = GESTURE_ACTION_MAPPINGS

    prop_primary = ("action", "swipe_gesture")
    prop_primary_label = "Swipe action"

    category_name = "Other gestures"

    required_props = [
        ("action", "swipe_gesture"),
        ("action", "swipe_gesture_options"),
    ]
