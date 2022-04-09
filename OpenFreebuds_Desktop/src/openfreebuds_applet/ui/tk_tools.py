import logging
import threading
import tkinter
from tkinter import ttk

import openfreebuds_backend
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t


class Config:
    theme = "light"


def in_other_thread(func):
    def internal(*args, **kwargs):
        threading.Thread(target=func, kwargs=kwargs, args=args).start()
    return internal


def set_theme(theme: str):
    if theme == "auto":
        theme = "dark" if openfreebuds_backend.is_dark_theme() else "light"
    Config.theme = theme


def create_themed():
    tk = tkinter.Tk()
    apply_theme(tk)

    return tk


def apply_theme(root):
    assets = utils.get_assets_path()

    try:
        root.tk.call("source", assets + "/ttk_theme/sun-valley.tcl")
        root.tk.call("set_theme", Config.theme)
    except tkinter.TclError:
        logging.exception("Can't set tkinter theme")


@in_other_thread
def message(content, title, callback=None):
    callback_used = threading.Event()
    root = create_themed()
    root.wm_title(title)

    def _on_ok():
        if callback is not None:
            callback()
            callback_used.set()
        root.destroy()

    frame = ttk.Frame(root)
    frame.pack()

    ttk.Label(frame, text=content).pack(padx=16, pady=16)
    ttk.Button(frame, text="OK", command=_on_ok).pack(padx=16, pady=12, anchor=tkinter.NW)

    root.mainloop()
    if not callback_used.is_set() and callback is not None:
        callback()
    root = None


@in_other_thread
def confirm(content, title, callback=None):
    callback_used = threading.Event()
    root = create_themed()
    root.wm_title(title)

    def _on_yes():
        if callback is not None:
            callback(True)
            callback_used.set()
        root.destroy()

    def _on_no():
        if callback is not None:
            callback(False)
            callback_used.set()
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

    root.mainloop()
    if not callback_used.is_set() and callback is not None:
        callback(False)
    root = None
