from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui.settings_ui.device_options.options import *


class DeviceSettingsTab(ttk.Frame):
    def __init__(self, parent: tkinter.Toplevel, manager: FreebudsManager, settings: SettingsStorage):
        super().__init__(parent)
        device = manager.device

        self.manager = manager
        self.device = device
        self.settings = settings
        self.parent = parent
        self.is_recording = False
        self.grid_columnconfigure(0, weight=1)

        self._add_device_info()
        self._add_device_settings()

    def _add_device_settings(self):
        if self.manager.state != FreebudsManager.STATE_CONNECTED:
            return

        option_views = [
            AutoPauseOption(),
            SeparateLongTapLeft(),
            DoubleTapOptionView(),
            VoiceLanguageOption(),
            BaseActionSelectView("power_button"),
            BaseActionSelectView("long_tap"),
        ]

        glob_y = 20

        for option in option_views:
            option.init(self, self.device)
            if option.is_available():
                option.build(glob_y)
                glob_y += option.count_rows

    def _add_device_info(self):
        # Device info
        label_font = tkinter.font.Font(weight="bold")
        ttk.Label(self, text=self.settings.device_name, font=label_font) \
            .grid(row=0, padx=16, pady=16, sticky=tkinter.NW)
        ttk.Label(self, text="Bluetooth Address") \
            .grid(row=1, padx=16, pady=4, sticky=tkinter.NW)
        ttk.Label(self, text=self.settings.address) \
            .grid(row=1, padx=16, pady=4, column=1, sticky=tkinter.NW)

        row_counter = 2
        if self.manager.state == FreebudsManager.STATE_CONNECTED:
            info_props = self.device.find_group("info")
            for a in info_props:
                ttk.Label(self, text=a)\
                    .grid(row=row_counter, padx=16, pady=4, sticky=tkinter.NW)
                ttk.Label(self, text=info_props[a])\
                    .grid(row=row_counter, column=1, padx=16, pady=4, sticky=tkinter.NW)
                row_counter += 1

    def _do_unpair(self):
        self.settings.address = ""
        self.settings.device_name = ""
        self.settings.write()

        self.manager.close(lock=False)
        self.parent.destroy()
