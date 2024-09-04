from openfreebuds_qt.app.module.common import OfbQtCommonModule


class OfbQtCommonWithShortcutsModule(OfbQtCommonModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.shortcut_names = {
            "connect": self.tr("Connect device"),
            "disconnect": self.tr("Disconnect device"),
            "toggle_connect": self.tr("Connect/disconnect device"),
            "next_mode": self.tr("Next noise control mode"),
            "mode_normal": self.tr("Disable noise control"),
            "mode_cancellation": self.tr("Enable noise cancellation"),
            "mode_awareness": self.tr("Enable awareness mode"),
            "enable_low_latency": self.tr("Enable low-latency mode"),
        }
