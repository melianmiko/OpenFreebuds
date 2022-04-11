import tkinter.font
import webbrowser
from tkinter import ttk

from PIL import Image, ImageTk
from mtrayapp import Menu

import openfreebuds_backend
from openfreebuds import cli_io
from openfreebuds_applet import utils
from openfreebuds_applet.ui import settings_ui, tk_tools
from openfreebuds_applet.l18n import t


@tk_tools.ui_thread
def about_window():
    version, debug = utils.get_version()
    logo_path = utils.get_assets_path() + "/icon.png"

    def website():
        webbrowser.open("https://melianmiko.ru/openfreebuds")

    def source():
        webbrowser.open("https://github.com/melianmiko/OpenFreebuds")

    tk = tkinter.Toplevel()
    tk.wm_title("About OpenFreebuds")

    frame = ttk.Frame(tk)
    frame.grid()
    frame.grid_columnconfigure(1, weight=1)

    # logo = tkinter.PhotoImage(file=logo_path, width=48, height=48)
    logo = Image.open(logo_path)
    logo = logo.resize((72, 72))
    logo = ImageTk.PhotoImage(logo)
    ttk.Label(tk, image=logo).grid(pady=16, padx=16, rowspan=30, sticky=tkinter.NW)

    h1_font = tkinter.font.Font(size=12, weight="bold")
    ttk.Label(tk, text="OpenFreebuds {}".format(version), font=h1_font)\
        .grid(row=10, column=1, pady=16, padx=16, columnspan=3, sticky=tkinter.NW)
    ttk.Label(tk, text="by melianmiko")\
        .grid(row=11, column=1, padx=16, pady=4, columnspan=3, sticky=tkinter.NW)
    ttk.Label(tk, text="available under GPLv3 license")\
        .grid(row=12, column=1, padx=16, pady=4, columnspan=3, sticky=tkinter.NW)

    ttk.Button(tk, text=t('open_website'), command=website)\
        .grid(row=20, column=1, padx=16, pady=16)
    ttk.Button(tk, text=t('open_github'), command=source)\
        .grid(row=20, column=2, padx=4, pady=16)

    tk.mainloop()


class ApplicationMenuPart(Menu):
    """
    Base application settings_ui menu part.
    """

    def __init__(self, applet):
        super().__init__()
        self.applet = applet

    def on_build(self):
        if not self.applet.settings.compact_menu:
            self.add_separator()

        self.add_item(t("action_settings"), self.open_settings)
        self.add_item(t("action_about"), about_window)
        self.add_separator()

        if self.applet.settings.enable_debug_features:
            self.add_item("DEV: Run command", self.do_command)
            self.add_item("DEV: Show logs", self.show_log)
            self.add_separator()

        self.add_item(t("action_exit"), self.applet.exit)

        if self.applet.settings.compact_menu:
            self.wrap(t("submenu_app"))

    def open_settings(self):
        settings_ui.open_app_settings(self.applet)

    def show_log(self):
        value = self.applet.log.getvalue()
        path = str(utils.get_app_storage_dir()) + "/last_log.txt"
        with open(path, "w") as f:
            f.write(value)

        openfreebuds_backend.open_file(path)

    def do_command(self):
        openfreebuds_backend.ask_string("openfreebuds>", self.on_command)

    def on_command(self, result):
        if result is None or result == "":
            return

        command = result.split(" ")
        result = cli_io.dev_command(self.applet.manager.device, command)
        self.application.message_box(result, "Dev mode")
