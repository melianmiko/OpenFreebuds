import logging
import threading
import tkinter
from tkinter import ttk

import openfreebuds_backend
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t

log = logging.getLogger("TkinterTools")


class Config:
    theme = "light"
    tk_root = None          # type: tkinter.Tk


def ui_thread(func):
    def _inner(*args):
        get_root().after_idle(func, *args)
    return _inner


def setup_window(window: tkinter.Toplevel):
    assets = utils.get_assets_path()

    window.iconphoto(False, tkinter.PhotoImage(file=assets + "/icon.png"))


def get_root():
    def th():
        log.debug("Starting UI thread...")
        Config.tk_root = tkinter.Tk()
        apply_theme(Config.tk_root)
        Config.tk_root.withdraw()
        complete.set()
        Config.tk_root.mainloop()
        Config.tk_root = None

    if Config.tk_root is None:
        complete = threading.Event()
        threading.Thread(target=th).start()
        complete.wait()

    return Config.tk_root


def apply_theme(root):
    assets = utils.get_assets_path()

    try:
        root.tk.call("source", assets + "/ttk_theme/sun-valley.tcl")
        root.tk.call("set_theme", Config.theme)
    except tkinter.TclError:
        logging.exception("Can't set tkinter theme")


def stop_ui():
    if Config.tk_root is None:
        return

    @ui_thread
    def _int():
        Config.tk_root.destroy()
        Config.tk_root = None

    _int()


def set_theme(theme: str):
    if theme == "auto":
        theme = "dark" if openfreebuds_backend.is_dark_theme() else "light"

    @ui_thread
    def _int():
        try:
            Config.tk_root.tk.call("set_theme", Config.theme)
        except tkinter.TclError:
            logging.exception("Can't set tkinter theme")

    Config.theme = theme
    if Config.tk_root is not None:
        _int()


@ui_thread
def message(content, title, callback=None, parent=None):
    callback_used = threading.Event()
    root = tkinter.Toplevel(parent)
    root.wm_title(title)
    root.wm_resizable(False, False)

    setup_window(root)

    def _on_ok():
        if callback is not None:
            callback()
            callback_used.set()
        root.destroy()

    frame = ttk.Frame(root)
    frame.pack()

    ttk.Label(frame, text=content).pack(padx=16, pady=16)
    ttk.Button(frame, text="OK", style="Accent.TButton", command=_on_ok)\
        .pack(padx=16, pady=12, anchor=tkinter.NW)

    root.tk.eval(f'tk::PlaceWindow {str(root)} center')
    root.protocol("WM_DELETE_WINDOW", _on_ok)


@ui_thread
def confirm(content, title, callback=None, parent=None):
    root = tkinter.Toplevel(parent)
    root.wm_title(title)
    root.wm_resizable(False, False)

    setup_window(root)

    def _on_yes():
        if callback is not None:
            callback(True)
        root.destroy()

    def _on_no():
        if callback is not None:
            callback(False)
        root.destroy()

    frame = ttk.Frame(root)
    frame.grid()
    frame.grid_columnconfigure(2, weight=1)

    ttk.Label(frame, text=content)\
        .grid(padx=16, pady=16, column=0, row=0, columnspan=3)
    ttk.Button(frame, text=t("yes"), style="Accent.TButton", command=_on_yes)\
        .grid(padx=16, pady=12, column=0, row=1)
    ttk.Button(frame, text=t("no"), command=_on_no)\
        .grid(padx=0, pady=12, column=1, row=1)

    root.tk.eval(f'tk::PlaceWindow {str(root)} center')
    root.protocol("WM_DELETE_WINDOW", _on_no)
