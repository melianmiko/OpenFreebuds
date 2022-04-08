import logging
import tkinter

from openfreebuds_applet import utils


def create_themed(theme):
    tk = tkinter.Tk()
    assets = utils.get_assets_path()

    try:
        tk.tk.call("source", assets + "/ttk_theme/sun-valley.tcl")
        tk.tk.call("set_theme", theme)
    except tkinter.TclError:
        logging.exception("Can't set tkinter theme")

    return tk
