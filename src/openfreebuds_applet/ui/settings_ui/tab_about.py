import tkinter
import webbrowser
from tkinter import ttk

import openfreebuds_backend
from openfreebuds.device import SUPPORTED_DEVICES
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t, get_current_lang
from openfreebuds_applet.dialog import dev_console
from openfreebuds_applet.utils import get_app_storage_dir

LINK_TRANSLATE = "https://mmk.pw/en/openfreebuds/translate"


def make_about(parent, applet):
    version = utils.get_version()

    def website():
        if get_current_lang() == "ru_RU":
            url = "https://mmk.pw/openfreebuds"
        else:
            url = "https://mmk.pw/en/openfreebuds"
        webbrowser.open(url)

    def source():
        webbrowser.open("https://github.com/melianmiko/openfreebuds")

    def do_console(_):
        dev_console.start(applet.manager)

    frame = ttk.Frame(parent)
    frame.grid_columnconfigure(2, weight=1)

    h1_font = tkinter.font.Font(size=14, weight="bold")
    h2_font = tkinter.font.Font(weight="bold")

    ttk.Label(frame, text="OpenFreebuds {}".format(version), font=h1_font)\
        .grid(row=10, pady=16, padx=16, columnspan=3, sticky=tkinter.NW)
    ttk.Label(frame, text="by melianmiko")\
        .grid(row=11, padx=16, pady=4, columnspan=3, sticky=tkinter.NW)
    ttk.Label(frame, text="available under GPLv3 license")\
        .grid(row=12, padx=16, pady=4, columnspan=3, sticky=tkinter.NW)

    ttk.Button(frame, text=t('Website'), command=website)\
        .grid(row=20, padx=16, pady=12)
    ttk.Button(frame, text=t('Source code'), command=source)\
        .grid(row=20, column=1, padx=4, pady=12)

    link = ttk.Label(frame, text=t("Help with translation"), foreground="#04F", cursor="hand2")
    link.bind("<Button-1>", lambda _: webbrowser.open(LINK_TRANSLATE))
    link.grid(row=21, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

    # List supported devices
    ttk.Label(frame, text=t("Supported devices"), font=h2_font)\
        .grid(row=30, padx=16, pady=16, columnspan=3, sticky=tkinter.NW)

    counter = 31
    for name, (support_level, _) in SUPPORTED_DEVICES.items():
        if support_level != "full":
            continue
        ttk.Label(frame, text=f"- {name}")\
            .grid(row=counter, padx=16, pady=4, columnspan=3, sticky=tkinter.NW)
        counter += 1
    for name, (support_level, _) in SUPPORTED_DEVICES.items():
        if support_level != "partial":
            continue
        ttk.Label(frame, text=f"- {name} ({t('Partial compatibility')})")\
            .grid(row=counter, padx=16, pady=4, columnspan=3, sticky=tkinter.NW)
        counter += 1

    # Adv. label
    ttk.Label(frame, text=t("Extra options"), font=h2_font)\
        .grid(row=60, padx=16, pady=16, columnspan=3, sticky=tkinter.NW)

    # App dir button
    link = ttk.Label(frame, text=t("Open config directory..."), foreground="#04F", cursor="hand2")
    link.bind("<Button-1>", lambda _: openfreebuds_backend.open_in_file_manager(str(get_app_storage_dir())))
    link.grid(row=61, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

    # Console button
    link = ttk.Label(frame, text=t("Start device console (danger!)..."), foreground="#04F", cursor="hand2")
    link.bind("<Button-1>", do_console)
    link.grid(row=62, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

    return frame
