from tkinter import ttk

from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import tk_tools
from openfreebuds_applet.ui.settings_ui.tab_application import AppSettingsTab
from openfreebuds_applet.ui.settings_ui.tab_device import DeviceSettingsTab
from openfreebuds_applet.ui.settings_ui.tab_hotkeys import HotkeysSettingsTab


@tk_tools.main_window
def open_app_settings(applet):
    tk = tk_tools.create_themed()
    tk.wm_title(t("settings_title"))
    tk.wm_resizable(False, False)

    frame = ttk.Frame(tk)
    frame.grid()

    notebook = ttk.Notebook(frame)
    notebook.grid(column=0, row=0, sticky="nesw")

    if applet.manager.state == FreebudsManager.STATE_CONNECTED:
        notebook.add(DeviceSettingsTab(tk, applet.manager, applet.settings),
                     text=t("settings_tab_device"))

    notebook.add(AppSettingsTab(notebook, applet, tk), text=t("settings_tab_app"))
    notebook.add(HotkeysSettingsTab(notebook, applet), text=t("settings_tab_hotkeys"))

    tk.mainloop()


@tk_tools.main_window
def open_device_settings(device, settings):
    tk = tk_tools.create_themed()
    tk.wm_title(settings.device_name)
    tk.wm_resizable(False, False)

    DeviceSettingsTab(tk, device, settings)
    tk.mainloop()
