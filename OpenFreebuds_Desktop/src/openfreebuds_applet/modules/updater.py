import glob
import json
import logging
import urllib.request
import webbrowser

import openfreebuds_backend
from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_UI_UPDATE_REQUIRED
from openfreebuds_applet import utils
from openfreebuds_applet.l18n import t

release_url = "https://st.melianmiko.ru/openfreebuds/release.json"
log = logging.getLogger("UpdateChecker")


class Data:
    show_messages = True
    has_update = False
    new_version = ""
    release_data = None
    tray_application = None


def get_result():
    return Data.has_update, Data.new_version


def start(applet):
    Data.show_messages = applet.settings.enable_update_dialog
    Data.tray_application = applet.tray_application
    applet.run_thread(_check_updates, "UpdateChecker", False)


def _check_updates():
    current_version, _ = utils.get_version()
    release_info = _fetch_release_info()
    if release_info is None:
        log.debug("Can't get release info, skip update check...")
        return

    release_data = json.loads(release_info)
    Data.release_data = release_data

    if release_data["version"] == current_version:
        return
    if get_platform_data() is None:
        return

    log.debug("Has new version: " + release_data["version"])

    Data.new_version = release_data["version"]
    Data.has_update = True

    if Data.show_messages and not is_repo_installed():
        show_update_message()

    event_bus.invoke(EVENT_UI_UPDATE_REQUIRED)


def show_update_message():
    release = Data.release_data
    platform_rel = get_platform_data()

    msg_base = "{}\n\n{}\n\nURL: {}\nFile size: {}".format(release["title"],
                                                           "\n".join(release["changelog"]),
                                                           platform_rel["url"],
                                                           sizeof_fmt(int(platform_rel["size"])))

    log.debug(msg_base)

    if is_repo_installed():
        Data.tray_application.message_box(t("update_message_auto").format(msg_base), "OpenFreebuds Updater")
    else:
        Data.tray_application.confirm_box(t("update_message").format(msg_base), "OpenFreebuds Updater",
                                          on_ui_result)


def on_ui_result(result):
    platform_rel = get_platform_data()
    if result:
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
            return d[a][0]

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
