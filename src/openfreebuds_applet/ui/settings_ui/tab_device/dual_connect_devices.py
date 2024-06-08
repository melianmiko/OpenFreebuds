from openfreebuds_applet.dialog import connection_center
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui.settings_ui.tab_device._generic import DeviceSettingsSection


class DualConnectDevicesSettingsSection(DeviceSettingsSection):
    category_name = "main"
    action_button = t("Connection center...")
    required_props = [
        ("config", "preferred_device"),
    ]

    def on_action_button_click(self):
        connection_center.start(self.device)
