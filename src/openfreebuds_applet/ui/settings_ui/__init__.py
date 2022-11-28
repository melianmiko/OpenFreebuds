import tkinter
from tkinter import ttk

from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import tk_tools
from openfreebuds_applet.ui.settings_ui import tab_about
from openfreebuds_applet.ui.settings_ui.tab_application import AppSettingsTab
from openfreebuds_applet.ui.settings_ui.tab_device import DeviceSettingsTab
from openfreebuds_applet.ui.settings_ui.tab_hotkeys import HotkeysSettingsTab


@tk_tools.ui_thread
def open_app_settings(applet):
    tk = tkinter.Toplevel()
    tk.wm_title(t("settings_title"))
    tk.wm_resizable(False, False)

    tk_tools.setup_window(tk)

    frame = ttk.Frame(tk)
    frame.grid()

    notebook = ttk.Notebook(frame)
    notebook.grid(column=0, row=0, sticky="nesw")

    if applet.settings.address != "":
        notebook.add(DeviceSettingsTab(tk, applet.manager, applet.settings), text=t("settings_tab_device"))

    notebook.add(AppSettingsTab(notebook, applet), text=t("settings_tab_app"))
    notebook.add(HotkeysSettingsTab(notebook, applet), text=t("settings_tab_hotkeys"))
    notebook.add(tab_about.make_about(notebook, applet), text=t("settings_tab_about"))

    tk.tk.eval(f'tk::PlaceWindow {str(tk)} center')
