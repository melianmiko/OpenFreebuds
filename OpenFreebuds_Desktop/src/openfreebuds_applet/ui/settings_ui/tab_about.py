import tkinter
import webbrowser
from tkinter import ttk

from PIL import ImageTk, Image

import openfreebuds.device
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t


def make_about(parent):
    version, debug = utils.get_version()

    def website():
        webbrowser.open(t("app_site_url"))

    def source():
        webbrowser.open("https://github.com/melianmiko/OpenFreebuds")

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

    ttk.Button(frame, text=t('open_website'), command=website)\
        .grid(row=20, padx=16, pady=16)
    ttk.Button(frame, text=t('open_github'), command=source)\
        .grid(row=20, column=1, padx=4, pady=16)

    # List supported devices
    ttk.Label(frame, text="Tested devices", font=h2_font)\
        .grid(row=30, padx=16, pady=16, columnspan=3, sticky=tkinter.NW)

    counter = 31
    for a in openfreebuds.device.DEVICE_PROFILES:
        ttk.Label(frame, text="- {}".format(a)).grid(row=counter, padx=16, pady=4, columnspan=3, sticky=tkinter.NW)
        counter += 1

    return frame
