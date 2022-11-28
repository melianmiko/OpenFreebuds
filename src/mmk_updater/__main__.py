from _base import UpdaterTool
from ui_tkinter import TkinterUiMod
import logging

ui_mod = TkinterUiMod()

logging.basicConfig(level=logging.DEBUG)
UpdaterTool("https://st.melianmiko.ru/openfreebuds/release.json", "0.1", ui_mod).start()
