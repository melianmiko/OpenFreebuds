from mmk_updater.ui_tkinter import TkinterUiMod

from openfreebuds_applet.ui import tk_tools


class FreebudsUpdateUiMod(TkinterUiMod):
    def __init__(self):
        super().__init__()

    def init_tk(self):
        return tk_tools.get_root()
