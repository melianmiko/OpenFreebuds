import tkinter
import webbrowser
from tkinter import ttk

import openfreebuds.device
import openfreebuds_backend
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t
from openfreebuds_applet.dialog import dev_console
from openfreebuds_applet.utils import get_app_storage_dir

LINK_TRANSLATE = "https://crowdin.com/project/openfreebuds"

def make_about(parent, applet):
    version = utils.get_version()

    def website():
        webbrowser.open(t("app_site_url"))

    def source():
        webbrowser.open("https://github.com/melianmiko/openfreebuds")

    # TODO: Refactor report tool
    # def do_report(_):
    #     report = self_check.generate_report(applet)
    #     path = str(utils.get_app_storage_dir()) + "/report.txt"
    #     with open(path, "w") as f:
    #         f.write(report)
    #
    #     openfreebuds_backend.open_file(path)

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

    link = ttk.Label(frame, text=t("action_help_translate"), foreground="#04F", cursor="hand2")
    link.bind("<Button-1>", lambda _: webbrowser.open(LINK_TRANSLATE))
    link.grid(row=21, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

    # List supported devices
    ttk.Label(frame, text=t("category_tested"), font=h2_font)\
        .grid(row=30, padx=16, pady=16, columnspan=3, sticky=tkinter.NW)

    counter = 31
    for name in openfreebuds.device.SUPPORTED_DEVICES:
        ttk.Label(frame, text="- {}".format(name))\
            .grid(row=counter, padx=16, pady=4, columnspan=3, sticky=tkinter.NW)
        counter += 1

    # Adv. label
    ttk.Label(frame, text=t("category_extras"), font=h2_font)\
        .grid(row=60, padx=16, pady=16, columnspan=3, sticky=tkinter.NW)

    # Report button
    # link = ttk.Label(frame, text=t("action_mk_report"), foreground="#04F", cursor="hand2")
    # link.bind("<Button-1>", do_report)
    # link.grid(row=61, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

    # App dir button
    link = ttk.Label(frame, text=t("action_open_appdata"), foreground="#04F", cursor="hand2")
    link.bind("<Button-1>", lambda _: openfreebuds_backend.open_in_file_manager(str(get_app_storage_dir())))
    link.grid(row=61, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

    # Console button
    link = ttk.Label(frame, text=t("action_dev_console"), foreground="#04F", cursor="hand2")
    link.bind("<Button-1>", do_console)
    link.grid(row=62, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

    return frame
