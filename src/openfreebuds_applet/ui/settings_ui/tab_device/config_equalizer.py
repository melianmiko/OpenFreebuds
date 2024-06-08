from openfreebuds_applet.ui.i18n_mappings import EQ_PRESET_MAPPING
from openfreebuds_applet.ui.settings_ui.tab_device._generic_selectable import SelectableDeviceOption


class EqualizerSettingsSection(SelectableDeviceOption):
    prop_options = ("config", "equalizer_preset_options")
    prop_options_labels = EQ_PRESET_MAPPING

    prop_primary = ("config", "equalizer_preset")
    prop_primary_label = "Equalizer"

    category_name = "Sound preferences"

    required_props = [
        ("config", "equalizer_preset"),
        ("config", "equalizer_preset_options"),
    ]
