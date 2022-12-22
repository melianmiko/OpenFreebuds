import tkinter
import webbrowser
from tkinter import ttk

from PIL import ImageTk, Image

import openfreebuds.device
import openfreebuds_backend
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.ui import dev_console
from openfreebuds_applet.modules import self_check


def make_about(parent, applet):
    version, debug = utils.get_version()

    def website():
        webbrowser.open(t("app_site_url"))

    def source():
        webbrowser.open("https://github.com/melianmiko/OpenFreebuds")

    def do_report(_):
        report = self_check.generate_report(applet)
        path = str(utils.get_app_storage_dir()) + "/report.txt"
        with open(path, "w") as f:
            f.write(report)

        openfreebuds_backend.open_file(path)

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

    ttk.Button(frame, text=t('open_website'), command=website)\
        .grid(row=20, padx=16, pady=12)
    ttk.Button(frame, text=t('open_github'), command=source)\
        .grid(row=20, column=1, padx=4, pady=12)

    # List supported devices
    ttk.Label(frame, text=t("category_tested"), font=h2_font)\
        .grid(row=30, padx=16, pady=16, columnspan=3, sticky=tkinter.NW)

    counter = 31
    for a in openfreebuds.device.DEVICE_PROFILES:
        ttk.Label(frame, text="- {}".format(a)).grid(row=counter, padx=16, pady=4, columnspan=3, sticky=tkinter.NW)
        counter += 1

    # Adv. label
    ttk.Label(frame, text=t("category_extras"), font=h2_font)\
        .grid(row=60, padx=16, pady=16, columnspan=3, sticky=tkinter.NW)

    # Report button
    link = ttk.Label(frame, text=t("action_mk_report"), foreground="#04F", cursor="hand2")
    link.bind("<Button-1>", do_report)
    link.grid(row=61, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

    # Console button
    link = ttk.Label(frame, text=t("action_dev_console"), foreground="#04F", cursor="hand2")
    link.bind("<Button-1>", do_console)
    link.grid(row=62, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

    return frame
