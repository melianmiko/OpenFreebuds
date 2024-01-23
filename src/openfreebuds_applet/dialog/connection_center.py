import tkinter

from openfreebuds.device import BaseDevice
from openfreebuds.logger import create_log
from openfreebuds_applet.ui import tk_tools

log = create_log("ConnCenter")


@tk_tools.ui_thread
def start(device: BaseDevice):
    root = tkinter.Toplevel()
    root.wm_title("Connection center")
    root.geometry("400x600")
    root.wm_resizable(False, False)

    tk_tools.setup_window(root)

    # TODO: design this
