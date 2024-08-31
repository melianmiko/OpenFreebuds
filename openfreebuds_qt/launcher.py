import asyncio
import logging
from argparse import ArgumentParser

from PyQt6.QtWidgets import QApplication

import openfreebuds
from openfreebuds import OfbEventKind, IOpenFreebuds
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.async_qt_loop import qt_app_entrypoint
from openfreebuds_qt.config.config_lock import ConfigLock
from openfreebuds_qt.constants import IGNORED_LOG_TAGS
from openfreebuds_qt.main import OfbQtMainWindow
from openfreebuds_qt.version_info import VERSION

log = create_logger("OfbQtLauncher")

parser = ArgumentParser(
    prog="openfreebuds_qt",
    description="Client application for HUAWEI Bluetooth headphones",
    epilog=f"by melianmiko | mmk.pw | {VERSION}"
)

parser.add_argument("-v", "--verbose",
                    action="store_true",
                    help="Verbose log output")
parser.add_argument("-l", "--dont-ignore-logs",
                    action="store_true",
                    help="Don't exclude third-party libraries logs")
parser.add_argument('-c', '--client',
                    action="store_true",
                    help="Client-mode, allows to start multiple app instances from the same user")
parser.add_argument("shortcut",
                    nargs="?", default="",
                    help="Execute shortcut operation in using OpenFreebuds")


@qt_app_entrypoint(OfbQtMainWindow)
async def main(app: QApplication, window: OfbQtMainWindow):
    try:
        args = parser.parse_args()

        logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARN)
        if not args.dont_ignore_logs:
            for tag in IGNORED_LOG_TAGS:
                logging.getLogger(tag).disabled = True

        ofb = await openfreebuds.create()

        window.ofb = ofb
        window.application = app
        ConfigLock.acquire()

        if args.shortcut != "":
            return await _run_shortcut(args.shortcut, ofb, window, app)

        if ofb.role == "client" and not ConfigLock.owned and not args.client:
            return await _bring_window_up(ofb, app)

        log.info(f"Starting OfbQtMainWindow, ofb_role={ofb.role}, config_owned={ConfigLock.owned}")
        await window.boot()
        window.show()
    except SystemExit as e:
        app.exit(e.args[0])
        ConfigLock.release()
        return


async def _bring_window_up(ofb: IOpenFreebuds, app: QApplication):
    print("Already running, will only bring settings window up")
    print("If you really need another instance, add --client")
    await ofb.send_message(OfbEventKind.QT_BRING_SETTINGS_UP)
    app.exit(0)


async def _run_shortcut(shortcut: str, ofb: IOpenFreebuds, window: OfbQtMainWindow, app: QApplication):
    if ofb.role == "standalone":
        await window.restore_device()
        while await ofb.get_state() != IOpenFreebuds.STATE_CONNECTED:
            log.debug("Waiting for device connect...")
            await asyncio.sleep(1)

    await ofb.run_shortcut(shortcut)
    app.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
