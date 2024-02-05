import tkinter
from tkinter import ttk

from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import tk_tools
from openfreebuds_applet.ui.settings_ui import tab_about
from openfreebuds_applet.ui.settings_ui.tab_application import AppSettingsTab
from openfreebuds_applet.ui.settings_ui.tab_device import DeviceSettingsTab
from openfreebuds_applet.ui.settings_ui.tab_modules import ModulesSettingsTab

SETTINGS_SIZES = [550, 650]


@tk_tools.ui_thread
def open_app_settings(applet):
    tk = tkinter.Toplevel(class_="openfreebuds")
    tk.wm_title(t("settings_title"))
    tk.wm_resizable(False, False)

    w, h = SETTINGS_SIZES
    tk.geometry(f"{w}x{h}")

    tk_tools.setup_window(tk)

    frame = ttk.Frame(tk)
    frame.grid()

    notebook = ttk.Notebook(frame, height=h, width=w)
    notebook.grid(column=0, row=0, sticky="nesw")

    if applet.settings.address != "":
        device_main_tab = DeviceSettingsTab(tk, applet.manager, applet.settings,
                                            allowed_categories=[
                                                "main",
                                                "setup_category_sound_quality",
                                                "setup_category_config",
                                            ])
        device_gestures_tab = DeviceSettingsTab(tk, applet.manager, applet.settings,
                                                with_header=False,
                                                allowed_categories=[
                                                    "category_double_tap",
                                                    "category_long_tap",
                                                    "category_gestures_misc",
                                                ])
        notebook.add(device_main_tab, text=t("settings_tab_device"))
        notebook.add(device_gestures_tab, text=t("setup_category_gestures"))

    notebook.add(AppSettingsTab(notebook, applet), text=t("settings_tab_app"))
    # notebook.add(ModulesSettingsTab(notebook, applet), text=t("settings_tab_modules"))
    notebook.add(tab_about.make_about(notebook, applet), text=t("settings_tab_about"))

    tk.tk.eval(f'tk::PlaceWindow {str(tk)} center')
