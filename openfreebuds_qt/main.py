import asyncio
import logging
import sys
from typing import Optional

from PyQt6.QtCore import QLibraryInfo, QLocale, QTranslator
from qasync import QEventLoop

from openfreebuds import IOpenFreebuds, create as create_ofb, OfbEventKind
from openfreebuds.utils.logger import setup_logging, screen_handler, create_logger
from openfreebuds_qt.app.main import OfbQtMainWindow
from openfreebuds_qt.config import OfbQtConfigParser, ConfigLock
from openfreebuds_qt.constants import IGNORED_LOG_TAGS, I18N_PATH, STORAGE_PATH
from openfreebuds_qt.generic import IOfbQtApplication
from openfreebuds_qt.tray.main import OfbTrayIcon
from openfreebuds_qt.utils import OfbQtDeviceAutoSelect, OfbQtHotkeyService, list_available_locales
from openfreebuds_qt.utils.mpris.service import OfbQtMPRISHelperService

log = create_logger("OfbQtApplication")


class OfbQtApplication(IOfbQtApplication):
    def __init__(self, args):
        super().__init__(sys.argv)

        self.args = args

        # Config folder
        if not STORAGE_PATH.is_dir():
            STORAGE_PATH.mkdir()

        # Services and UI parts
        self.config = OfbQtConfigParser.get_instance()
        self.ofb: Optional[IOpenFreebuds] = None
        self.auto_select: Optional[OfbQtDeviceAutoSelect] = None
        self.hotkeys: Optional[OfbQtHotkeyService] = None
        self.mpris: Optional[OfbQtMPRISHelperService] = None
        self.tray: Optional[OfbTrayIcon] = None
        self.main_window: Optional[OfbQtMainWindow] = None

        # Setup logging
        setup_logging(args.verbose)
        if not args.verbose:
            screen_handler.setLevel(logging.WARN)
        if not args.dont_ignore_logs:
            for tag in IGNORED_LOG_TAGS:
                logging.getLogger(tag).disabled = True

        # App configuration
        ConfigLock.acquire()

        # Qt base configs
        self.setApplicationName("OpenFreebuds")
        self.setDesktopFileName("openfreebuds")

        # Qt i18n
        locale = self._detect_locale()
        self.translator = QTranslator()
        self.translator.load(str(I18N_PATH / f"{locale}.qm"))
        self.installTranslator(self.translator)
        self.qt_translator = QTranslator()
        self.qt_translator.load("qtbase_" + locale,
                                QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
        self.installTranslator(self.qt_translator)

        # AsyncQt preparations
        self.event_loop = QEventLoop(self)
        self.close_event = asyncio.Event()
        self.aboutToQuit.connect(self.close_event.set)

    async def boot(self):
        try:
            await self._stage_setup_ofb()

            if self.args.shortcut != "":
                return await self._stage_shortcut()
            if self.ofb.role == "client" and not ConfigLock.owned and not self.args.client:
                return await self._trigger_settings()

            log.info(f"Starting OfbQtMainWindow, ofb_role={self.ofb.role}, config_owned={ConfigLock.owned}")

            # Initialize services
            self.hotkeys = OfbQtHotkeyService.get_instance(self.ofb)
            self.mpris = OfbQtMPRISHelperService.get_instance(self.ofb)
            self.auto_select = OfbQtDeviceAutoSelect(self.ofb)
            self.tray = OfbTrayIcon(self)
            self.main_window = OfbQtMainWindow(self)

            if self.ofb.role == "standalone":
                await self.restore_device()
                await self.auto_select.boot()

            self.hotkeys.start()
            await self.mpris.start()
            await self.tray.boot()
            await self.main_window.boot()

            # Show UI
            self.tray.show()
            if self.args.settings:
                self.main_window.show()
        except SystemExit as e:
            self.qt_app.exit(e.args[0])
            ConfigLock.release()
            return
        except Exception:
            log.exception("App boot failed")

    async def exit(self, ret_code: int = 0):
        await self.tray.close()
        self.main_window.close()

        if self.ofb.role == "standalone":
            await self.ofb.destroy()

        return self._exit(ret_code)

    def _detect_locale(self):
        locale = self.config.get("ui", "language", "auto")
        available_locales = list_available_locales()

        if locale == "auto":
            locale = QLocale.system().name()
        if locale not in available_locales:
            locale = locale.split("_")[0]
            if locale not in available_locales:
                locale = "en"

        log.info(f"Going to use {locale} from {available_locales}")
        return locale

    def _exit(self, ret_code: int):
        ConfigLock.release()
        return self.qt_app.exit(ret_code)

    async def _stage_setup_ofb(self):
        self.ofb = await create_ofb()

        if self.args.virtual_device:
            log.info(f"Will boot with virtual device: {self.args.virtual_device}")
            await self.ofb.start("Debug: Virtual device", self.args.virtual_device)

    async def _trigger_settings(self):
        print("Already running, will only bring settings window up")
        print("If you really need another instance, add --client")
        await self.ofb.send_message(OfbEventKind.QT_BRING_SETTINGS_UP)
        self._exit(0)

    async def _stage_shortcut(self):
        if self.ofb.role == "standalone":
            await self.restore_device()
            while await self.ofb.get_state() != IOpenFreebuds.STATE_CONNECTED:
                log.debug("Waiting for device connect...")
                await asyncio.sleep(1)

        await self.ofb.run_shortcut(self.args.shortcut)
        self._exit(0)

    async def restore_device(self):
        name = self.config.get("device", "name", None)
        address = self.config.get('device', "address", None)
        if address is not None:
            log.info(f"Restore device name={name}, address={address}")
            await self.ofb.start(name, address)

    def exec_async(self):
        self.event_loop.create_task(self.boot())
        self.event_loop.run_until_complete(self.close_event.wait())
        self.event_loop.close()
