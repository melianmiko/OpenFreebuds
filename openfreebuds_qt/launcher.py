import asyncio
import logging
from argparse import ArgumentParser

from PyQt6.QtWidgets import QApplication

import openfreebuds
from openfreebuds import OfbEventKind, IOpenFreebuds
from openfreebuds.utils.logger import create_logger, screen_handler, setup_logging
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
parser.add_argument('-s', '--settings',
                    action="store_true",
                    help="Open settings after launch")
parser.add_argument('--virtual-device',
                    help="Use virtual debug device, for UI testing")
parser.add_argument("shortcut",
                    nargs="?", default="",
                    help="Execute shortcut operation in using OpenFreebuds")


@qt_app_entrypoint(OfbQtMainWindow)
async def main(app: QApplication, window: OfbQtMainWindow):
    app.setApplicationName("OpenFreebuds")
    app.setDesktopFileName("openfreebuds")

    try:
        args = parser.parse_args()
        await _stage_setup_logging(args)
        ofb, initialized = await _stage_setup_ofb(args)

        window.ofb = ofb
        window.application = app
        ConfigLock.acquire()

        if args.shortcut != "":
            return await _run_shortcut(args.shortcut, ofb, window, app)

        if ofb.role == "client" and not ConfigLock.owned and not args.client:
            return await _trigger_settings(ofb, app)

        log.info(f"Starting OfbQtMainWindow, ofb_role={ofb.role}, config_owned={ConfigLock.owned}")
        await window.boot(not initialized)
        if args.settings:
            window.show()
    except SystemExit as e:
        app.exit(e.args[0])
        ConfigLock.release()
        return


async def _stage_setup_logging(args):
    setup_logging(args.verbose)

    if not args.verbose:
        screen_handler.setLevel(logging.WARN)

    if not args.dont_ignore_logs:
        for tag in IGNORED_LOG_TAGS:
            logging.getLogger(tag).disabled = True


async def _stage_setup_ofb(args):
    ofb = await openfreebuds.create()

    if args.virtual_device:
        log.info(f"Will boot with virtual device: {args.virtual_device}")
        await ofb.start("Debug: Virtual device", args.virtual_device)
        initialized = True
    else:
        initialized = False

    return ofb, initialized


async def _trigger_settings(ofb: IOpenFreebuds, app: QApplication):
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
    main()
