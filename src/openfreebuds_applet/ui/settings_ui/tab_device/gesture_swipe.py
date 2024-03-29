from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class SwipeGestureSettingsSection(SelectableDeviceOption):
    prop_options = ("action", "swipe_gesture_options")
    prop_primary = ("action", "swipe_gesture")
    category_name = "category_gestures_misc"

    required_props = [
        ("action", "swipe_gesture"),
        ("action", "swipe_gesture_options"),
    ]
