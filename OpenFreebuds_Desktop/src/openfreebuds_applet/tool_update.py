import glob
import logging
import urllib.request
import webbrowser
from configparser import ConfigParser

import openfreebuds_backend
from openfreebuds import event_bus
from openfreebuds.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import tools
from openfreebuds_applet.l18n import t

release_url = "https://st.melianmiko.ru/openfreebuds/release.ini"
log = logging.getLogger("UpdateChecker")


class Data:
    show_messages = True
    has_update = False
    new_version = ""
    release_data = None


def get_result():
    return Data.has_update, Data.new_version


def start(applet):
    Data.show_messages = applet.settings.enable_update_dialog
    tools.run_thread_safe(_check_updates, "UpdateChecker", False)


def _check_updates():
    current_version, _ = tools.get_version()
    release_info = _fetch_release_info()
    if release_info is None:
        log.debug("Can't get release info, skip update check...")
        return

    release_data = ConfigParser()
    release_data.read_string(release_info)

    Data.release_data = release_data

    if release_data["release"]["version"] == current_version:
        return
    if get_platform_data() is None:
        return

    log.debug("Has new version: " + release_data["release"]["version"])

    Data.new_version = release_data["release"]["version"]
    Data.has_update = True

    if Data.show_messages and not is_repo_installed():
        show_update_message()

    event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


def show_update_message():
    release = Data.release_data["release"]
    platform_rel = get_platform_data()

    msg_base = "{}{}\n\nURL: {}\nFile size: {}".format(release["title"],
                                                       release["changelog"],
                                                       platform_rel["url"],
                                                       sizeof_fmt(int(platform_rel["size"])))

    log.debug(msg_base)

    if is_repo_installed():
        openfreebuds_backend.show_message(t("update_message_auto").format(msg_base))
        result = -1
    else:
        result = openfreebuds_backend.ask_question(t("update_message").format(msg_base))

    if result == openfreebuds_backend.UI_RESULT_YES:
        webbrowser.open(platform_rel["url"])


def is_repo_installed():
    ppa = glob.glob("/etc/apt/sources.list.d/melianmiko-ubuntu-software-*")

    if len(ppa) > 0:
        return True

    return False


def get_platform_data():
    d = Data.release_data
    sys_ids = openfreebuds_backend.get_system_id()

    for a in sys_ids:
        if a in d:
            return d[a]

    return None


# noinspection PyBroadException
def _fetch_release_info():
    try:
        result = urllib.request.urlopen(release_url)
        return result.read().decode("utf8")
    except Exception:
        return None


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"
