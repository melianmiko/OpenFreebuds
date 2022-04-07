# MelianMiko.ru updater, v0.9

import glob
import io
import json
import locale
import logging
import os
import platform
import subprocess
import threading
import time
import tkinter
import tkinter.font
import tkinter.messagebox
import urllib.request
from pathlib import Path
from tkinter import ttk

log = logging.getLogger("mmk-update")

BASE_LOCALE = {
    "has_update_title": "New version is available",
    "file_pattern": "File: {} ({})",
    "downloading": "Downloading file {}...",
    "download_btn": "Download update",
    "close_btn": "Close",
    "repo_install": "Install it via system package manager.",
    "manual_install": "Update downloaded, but we can't install it automatically.\nFile "
                      "was saved to {}.\nPlease install it after app close."
}

L18N = {
    "ru_RU": {
        "has_update_title": "Доступна новая версия",
        "file_pattern": "Будет загружен: {} ({})",
        "downloading": "Загружаем файл {}...",
        "download_btn": "Обновить",
        "close_btn": "Закрыть",
        "repo_install": "Установите обновление ч-з системный пакетный менеджер",
        "manual_install": "Обновление загружено, но мы не можем установить его автоматически.\nФайл"
                          "сохранён по пути {}. \nУстановите его, когда будет возможность."
    }
}


def t(k):
    lang = locale.getdefaultlocale()[0]
    if k in L18N[lang]:
        return L18N[lang][k]
    if k in BASE_LOCALE:
        return BASE_LOCALE[k]
    return k


class TkinterUiMod:
    # noinspection PyTypeChecker
    def __init__(self, parent):
        self.updater = parent
        self.tk_ask_root = None         # type: tkinter.Tk
        self.tk_dl_root = None         # type: tkinter.Tk
        self.tk_progress = None     # type: ttk.Progressbar
        self._window_ready = threading.Event()
        self.percent = 0

    def show_update_message(self):
        threading.Thread(target=self._show_update_message).start()

    def _show_update_message(self):
        root = tkinter.Tk()
        root.title = "Updater"

        self._add_base_update_info(root)

        ttk.Label(root, text=t("repo_install"),
                  justify=tkinter.LEFT,
                  padding=4).grid(column=0, row=3, columnspan=2)
        ttk.Button(root, text=t("close_btn"),
                   padding=4,
                   command=root.destroy).grid(column=0, row=4, padx=8, pady=8, columnspan=2)
        root.mainloop()

    def on_progress(self, percent):
        delta = percent - self.percent
        self.percent = percent
        self.tk_progress.step(delta)

    def show_download(self):
        self._window_ready = threading.Event()
        threading.Thread(target=self._show_download).start()
        self._window_ready.wait()

    def _show_download(self):
        root = tkinter.Tk()
        root.title = "Updater"
        self.tk_dl_root = root

        d = self.updater.get_download_data()
        fn = d[0].split("/")[-1]
        ttk.Label(root, text=t("downloading").format(fn),
                  justify=tkinter.LEFT,
                  padding=4).pack(expand=True, fill="both")

        progress = ttk.Progressbar(root, length=350)
        progress.pack(expand=True, fill="both")
        self.tk_progress = progress

        root.protocol("WM_DELETE_WINDOW", do_pass)
        root.after(1000, self._progress_auto_close)
        self._window_ready.set()
        root.mainloop()

    def _progress_auto_close(self):
        if self.percent >= 100:
            log.debug("download complete, closing self window")
            return
        self.tk_dl_root.after(1000, self._progress_auto_close)

    def ask_download(self):
        self._window_ready = threading.Event()
        threading.Thread(target=self._ask_download).start()
        self._window_ready.wait()

    def _ask_download(self):
        root = tkinter.Tk()
        root.title = "Updater"
        self.tk_ask_root = root
        self._add_base_update_info(root)

        url, size, tag = self.updater.get_download_data()
        fn = url.split("/")[-1]
        size = sizeof_fmt(size)

        ttk.Label(root, text=t("file_pattern").format(fn, size),
                  justify=tkinter.LEFT,
                  padding=4).grid(column=0, row=3, columnspan=2)

        ttk.Button(root, text=t("download_btn"),
                   padding=4,
                   command=self.updater.on_download_confirm).grid(column=0, row=4, padx=8, pady=8)
        ttk.Button(root, text=t("close_btn"),
                   padding=4,
                   command=self.updater.on_download_cancel).grid(column=1, row=4, padx=8, pady=8)

        self._close_event = threading.Event()
        root.protocol("WM_DELETE_WINDOW", self.updater.on_download_cancel)
        self._window_ready.set()
        root.mainloop()

    def close_download_bar(self):
        try:
            self.tk_dl_root.destroy()
            self.tk_dl_root = None
            time.sleep(1)
        except tkinter.TclError:
            pass

    def close_ask_box(self):
        try:
            self.tk_ask_root.destroy()
            self.tk_ask_root = None
            time.sleep(1)
        except tkinter.TclError:
            pass

    def message_user_install(self):
        threading.Thread(target=self._message_user_install).start()

    def _message_user_install(self):
        path = self.updater.file_path
        root = tkinter.Tk()

        ttk.Label(root, text=t("manual_install").format(path),
                  padding=16).grid(column=0, row=0)
        ttk.Button(root, text="OK",
                   command=root.destroy).grid(column=0, row=1, padx=8, pady=8)
        root.mainloop()

    def _add_base_update_info(self, root):
        ttk.Label(root, text=t("has_update_title"),
                  justify=tkinter.LEFT,
                  font=tkinter.font.Font(size=16, weight="bold"),
                  padding=4).grid(column=0, row=0, columnspan=2)

        rel_data = self.updater.release_data
        rel_title = rel_data["version"] + ": " + rel_data["title"]
        rel_changes = ""
        for a in rel_data["changelog"]:
            rel_changes += a + "\n"
        rel_changes = rel_changes[:-1:]

        ttk.Label(root, text=rel_title,
                  justify=tkinter.LEFT,
                  padding=4).grid(column=0, row=1, columnspan=2)
        ttk.Label(root, text=rel_changes,
                  justify=tkinter.LEFT,
                  padding=4).grid(column=0, row=2, columnspan=2)


# -------------------------------------------------------------------------------------


class UpdaterTool:
    def __init__(self, release_url, current_version):
        self.release_url = release_url
        self.current_version = current_version
        self.release_data = {}
        self.file_path = ""
        self.ppa_glob = "/etc/apt/sources.list.d/melianmiko-ubuntu-software-*"

        self.ui_mod = TkinterUiMod(self)

        self._ui_result = False
        self._on_result = threading.Event()

    # overridable
    def should_show_update_ui(self):
        if self._has_ppa():
            log.debug("has ppa, don't show update ui")
            return False

        return self.release_data["version"] != self.current_version

    # overridable
    def on_release_data(self):
        pass

    def _has_ppa(self):
        g = glob.glob(self.ppa_glob)
        return len(g) > 0

    @staticmethod
    def _has_external_updater():
        return os.path.isfile("/usr/local/bin/yay") or os.path.isfile("/usr/bin/yay")

    def show_update_dialog(self):
        threading.Thread(target=self._run_updater_ui).start()

    def start(self):
        threading.Thread(target=self._process).start()

    def on_download_confirm(self):
        self._ui_result = True
        self._on_result.set()
        self.ui_mod.close_ask_box()

    def on_download_cancel(self):
        self._ui_result = False
        self._on_result.set()
        self.ui_mod.close_ask_box()

    def get_download_data(self):
        tag = "linux"
        if platform.system() == "Windows":
            tag = "windows"
        elif os.path.isfile("/usr/bin/dpkg") and "debian" in self.release_data:
            tag = "debian"

        if tag not in self.release_data:
            return "", 0, ""

        return self.release_data[tag][0]["url"], self.release_data[tag][0]["size"], tag

    # noinspection PyBroadException
    def _process(self):
        log.debug("fetching update info...")
        try:
            release_info = urllib.request.urlopen(self.release_url).read()
            release_info = release_info.decode("utf8")
        except Exception:
            log.exception("can't fetch release info")
            return

        self.release_data = json.loads(release_info)
        log.debug("latest release: " + self.release_data["version"])
        self.on_release_data()

        if not self.should_show_update_ui():
            log.debug("update ui shouldn't be shown")
            return

        self._run_updater_ui()

    def _run_updater_ui(self):
        if self._has_external_updater() or self._has_ppa():
            self.ui_mod.show_update_message()
            return

        if self.get_download_data()[0] == "":
            log.debug("no applicable link found")
            return

        # Ask user for download
        self._on_result.clear()
        self.ui_mod.ask_download()
        self._on_result.wait()

        if not self._ui_result:
            log.debug("user skipped update, bye")
            return

        # Prepare url, filename and filepath
        url, size, tag = self.get_download_data()
        fn = url.split("/")[-1]
        self.file_path = str(Path.home() / fn)

        # Download file
        self.ui_mod.show_download()
        log.debug("downloading {}".format(url))
        buff = self._download_with_progress(url)
        self.ui_mod.percent = 100

        # Trigger download stats
        log.debug("trigger download stats")
        req = urllib.request.Request("https://melianmiko.ru/api/goal",
                                     json.dumps({
                                         "target": self.release_data["app"],
                                         "tag": "update_" + tag
                                     }).encode("utf8"))
        resp = urllib.request.urlopen(req)
        log.debug(resp.read().decode('utf8'))

        # Write to file
        log.debug("writing to file {}".format(self.file_path))
        with open(self.file_path, "wb") as f:
            f.write(buff.getvalue())

        # If not windows, show message about user install
        if platform.system() != "Windows" or not fn.endswith(".exe"):
            self.ui_mod.message_user_install()
            return

        # If windows, run executable installer
        log.debug("Running windows installer...")
        no_console = subprocess.STARTUPINFO()
        no_console.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(self.file_path, startupinfo=no_console, shell=True)

    def _download_with_progress(self, url):
        with urllib.request.urlopen(url) as Response:
            length = Response.getheader('content-length')
            block_size = 1000000

            if length:
                length = int(length)
                block_size = max(4096, length // 20)

            log.debug("downloading file with length {}".format(length))

            buffer = io.BytesIO()
            downloaded = 0
            while True:
                part = Response.read(block_size)
                if not part:
                    break
                buffer.write(part)
                downloaded += len(part)
                if length:
                    perc = int((downloaded / length) * 100)
                    log.debug("downloaded {}".format(perc))
                    self.ui_mod.on_progress(perc)

        return buffer


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def do_pass():
    pass


if __name__ == "__main__":
    # test start
    logging.basicConfig(level=logging.DEBUG)
    UpdaterTool("https://st.melianmiko.ru/openfreebuds/release.json", "0.1").start()
    # while True:
    #     time.sleep(2)
