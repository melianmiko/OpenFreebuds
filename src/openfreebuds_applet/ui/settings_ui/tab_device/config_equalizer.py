from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class EqualizerSettingsSection(SelectableDeviceOption):
    prop_options = ("config", "equalizer_preset_options")
    prop_primary = ("config", "equalizer_preset")
    category_name = "setup_category_sound_quality"

    required_props = [
        ("config", "equalizer_preset"),
        ("config", "equalizer_preset_options"),
    ]
