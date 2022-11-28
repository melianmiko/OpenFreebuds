import glob
import io
import json
import logging
import os
import platform
import subprocess
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

log = logging.getLogger("mmk-update")


class DummyUiModule:
    def __init__(self):
        # noinspection PyTypeChecker
        self.updater = None     # type: UpdaterTool

    def on_bind(self, updater):
        self.updater = updater

    def show_ppa_update_message(self):
        pass

    def update_download_progress(self, value):
        pass

    def show_download_progress(self):
        pass

    def show_auto_update_message(self):
        pass

    def close_auto_update_message(self):
        pass

    def show_manual_install_message(self):
        pass


# -------------------------------------------------------------------------------------


class UpdaterTool:
    def __init__(self, release_url: str, current_version: str, ui_mod: DummyUiModule):
        self.release_url = release_url
        self.current_version = current_version
        self.release_data = {}
        self.file_path = ""
        self.ppa_glob = "/etc/apt/sources.list.d/melianmiko-ubuntu-software-*"

        self.ui_mod = ui_mod
        self.ui_mod.on_bind(self)

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
        self.ui_mod.close_auto_update_message()

    def on_download_cancel(self):
        self._ui_result = False
        self._on_result.set()
        self.ui_mod.close_auto_update_message()

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
            self.ui_mod.show_ppa_update_message()
            return

        if self.get_download_data()[0] == "":
            log.debug("no applicable link found")
            return

        # Ask user for download
        self._on_result.clear()
        self.ui_mod.show_auto_update_message()
        self._on_result.wait()

        if not self._ui_result:
            log.debug("user skipped update, bye")
            return

        time.sleep(1)
        log.debug("Preparing to download...")

        # Prepare url, filename and filepath
        url, size, tag = self.get_download_data()
        fn = url.split("/")[-1]
        self.file_path = str(Path.home() / fn)

        # Download file
        self.ui_mod.show_download_progress()
        log.debug("downloading {}".format(url))
        try:
            buff = self._download_with_progress(url)
            self.ui_mod.percent = 100
        except urllib.error.URLError:
            self.ui_mod.percent = -1
            return

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
            self.ui_mod.show_manual_install_message()
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
                    self.ui_mod.update_download_progress(perc)

        return buffer
