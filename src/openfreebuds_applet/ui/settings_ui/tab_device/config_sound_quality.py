from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class SoundQualitySettingsSection(SelectableDeviceOption):
    prop_options = ("config", "sound_quality_preference_options")
    prop_primary = ("config", "sound_quality_preference")
    category_name = "setup_category_config"

    required_props = [
        ("config", "sound_quality_preference"),
        ("config", "sound_quality_preference_options"),
    ]
