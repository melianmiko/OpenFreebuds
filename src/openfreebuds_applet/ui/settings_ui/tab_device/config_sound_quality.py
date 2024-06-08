from openfreebuds_applet.ui.i18n_mappings import SOUND_QUALITY_MAPPINGS
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class SoundQualitySettingsSection(SelectableDeviceOption):
    prop_options = ("config", "sound_quality_preference_options")
    prop_options_labels = SOUND_QUALITY_MAPPINGS

    prop_primary = ("config", "sound_quality_preference")
    prop_primary_label = "Sound preference"

    category_name = "Sound preferences"

    required_props = [
        ("config", "sound_quality_preference"),
        ("config", "sound_quality_preference_options"),
    ]
