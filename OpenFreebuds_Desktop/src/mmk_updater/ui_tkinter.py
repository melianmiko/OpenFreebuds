import logging
import platform
import threading
import tkinter
import tkinter.font
import tkinter.messagebox
import webbrowser
from tkinter import ttk

from ._base import DummyUiModule
from ._lc import t
from ._tools import sizeof_fmt

log = logging.getLogger("TkinterUpdateUI")


class TkinterUiMod(DummyUiModule):
    # noinspection PyTypeChecker
    def __init__(self):
        super().__init__()
        self.tk_ask_root = None         # type: tkinter.Tk
        self.tk_dl_root = None          # type: tkinter.Tk
        self.tk_msg_root = None         # type: tkinter.Tk
        self.tk_progress = None         # type: ttk.Progressbar
        self._window_ready = threading.Event()
        self.percent = 0
        self._sent_percent = 0

    # noinspection PyMethodMayBeStatic
    def mk_window(self) -> tkinter.Tk:
        root = tkinter.Tk()
        return root

    def show_ppa_update_message(self):
        def _internal():
            root = self.mk_window()
            root.wm_title("Updater")

            frame = ttk.Frame(root)
            frame.grid()

            self._add_base_update_info(frame, 1)

            ttk.Label(frame, text=t("repo_install"), justify=tkinter.LEFT) \
                .grid(column=0, row=4, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

            ttk.Button(frame, text=t("close_btn"), command=root.destroy) \
                .grid(column=0, row=5, padx=4, pady=4, sticky=tkinter.NW)

            root.mainloop()

        threading.Thread(target=_internal).start()

    def show_download_progress(self):
        def _internal():
            root = self.mk_window()
            root.wm_title(self.updater.release_data["app"])
            self.tk_dl_root = root

            d = self.updater.get_download_data()
            fn = d[0].split("/")[-1]
            label = t("downloading").format(fn)
            if platform.system() == "Windows":
                label += "\n" + t("downloading_run_after")

            frame = ttk.Frame(root)
            frame.pack()

            ttk.Label(frame, text=label, justify=tkinter.LEFT) \
                .pack(expand=True, fill="both", padx=16, pady=16)

            progress = ttk.Progressbar(frame, length=350)
            progress.pack(expand=True, fill="both", padx=16, pady=16)
            self.tk_progress = progress

            root.after(1000, self._progress_auto_close)
            self._window_ready.set()
            root.mainloop()

        self._window_ready = threading.Event()
        threading.Thread(target=_internal).start()
        self._window_ready.wait()

    def update_download_progress(self, value):
        self.percent = value

    def show_auto_update_message(self):
        def _internal():
            url, size, tag = self.updater.get_download_data()
            fn = url.split("/")[-1]
            size = sizeof_fmt(size)

            root = self.mk_window()
            root.wm_title(self.updater.release_data["app"])

            self.tk_ask_root = root

            frame = ttk.Frame(root)
            frame.grid()

            self._add_base_update_info(frame, 3)
            frame.grid_columnconfigure(2, weight=1)

            ttk.Label(frame, text=t("file_pattern").format(fn, size), justify=tkinter.LEFT) \
                .grid(column=0, row=4, columnspan=3, padx=16, pady=4, sticky=tkinter.NW)

            ttk.Button(frame, text=t("download_btn"), command=self.updater.on_download_confirm) \
                .grid(column=0, row=5, padx=4, pady=4, sticky=tkinter.NW)

            ttk.Button(frame, text=t("close_btn"), command=self.updater.on_download_cancel) \
                .grid(column=2, row=5, padx=4, pady=4, sticky=tkinter.NW)

            self._close_event = threading.Event()
            root.protocol("WM_DELETE_WINDOW", self.updater.on_download_cancel)
            self._window_ready.set()
            root.mainloop()

        self._window_ready = threading.Event()
        threading.Thread(target=_internal).start()
        self._window_ready.wait()

    def close_auto_update_message(self):
        try:
            self.tk_ask_root.destroy()
            self.tk_ask_root = None
        except tkinter.TclError:
            pass

    def show_manual_install_message(self):
        def _internal():
            path = self.updater.file_path
            root = self.mk_window()
            root.wm_title(self.updater.release_data["app"])

            self.tk_msg_root = root
            frame = ttk.Frame(root)
            frame.grid()

            ttk.Label(frame, text=t("manual_install").format(path), padding=16).grid(column=0, row=0)
            ttk.Button(frame, text="OK", command=self._message_user_install_ok)\
                .grid(column=0, row=1, padx=4, pady=4, sticky=tkinter.NW)
            frame.mainloop()

        threading.Thread(target=_internal).start()

    def _message_user_install_ok(self):
        self.tk_msg_root.destroy()
        self.tk_msg_root = None

    def _add_base_update_info(self, root, columns):
        ttk.Label(root, text=t("has_update_title").format(self.updater.release_data["app"]),
                  justify=tkinter.LEFT, font=tkinter.font.Font(weight="bold"))\
            .grid(column=0, row=0, padx=16, pady=8, columnspan=columns, sticky=tkinter.NW)

        rel_data = self.updater.release_data
        rel_title = rel_data["version"] + ": " + rel_data["title"]
        rel_changes = ""
        for a in rel_data["changelog"]:
            rel_changes += a + "\n"
        rel_changes = rel_changes[:-1:]

        ttk.Label(root, text=rel_title, justify=tkinter.LEFT, font=tkinter.font.Font(size=16))\
            .grid(column=0, row=1, padx=16, pady=4, columnspan=columns, sticky=tkinter.NW)
        ttk.Label(root, text=rel_changes, justify=tkinter.LEFT)\
            .grid(column=0, row=2, padx=16, pady=4, columnspan=columns, sticky=tkinter.NW)

        if "website" in self.updater.release_data:
            link = ttk.Label(root, text=t("site_btn"),
                             foreground="#04F",
                             cursor="hand2")
            link.bind("<Button-1>", self._open_site)
            link.grid(column=0, row=3, padx=16, pady=4, columnspan=columns, sticky=tkinter.NW)

    def _progress_auto_close(self):
        if self.percent >= 100:
            log.debug("download complete, closing self window")
            self._close_download_bar()
            return
        if self.percent < 0:
            font = tkinter.font.Font(weight="bold")
            tkinter.Label(self.tk_dl_root, text=t("dl_error"), font=font)\
                .pack(padx=16, pady=16)
            return
        self.tk_progress.step(self.percent - self._sent_percent)
        self._sent_percent = self.percent
        self.tk_dl_root.after(1000, self._progress_auto_close)

    def _close_download_bar(self):
        try:
            log.debug("close dl box from " + str(threading.get_ident()))
            self.tk_dl_root.destroy()
            self.tk_dl_root = None
            self.tk_progress = None
        except tkinter.TclError:
            pass

    # noinspection PyUnusedLocal
    def _open_site(self, ev):
        webbrowser.open(self.updater.release_data["website"])
