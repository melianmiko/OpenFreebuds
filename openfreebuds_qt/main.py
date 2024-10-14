import asyncio
import logging
import os
import sys
from contextlib import suppress
from typing import Optional

from PyQt6.QtCore import QLibraryInfo, QLocale, QTranslator, QT_VERSION_STR
from PyQt6.QtWidgets import QMessageBox, QSystemTrayIcon
from qasync import QEventLoop

from openfreebuds import IOpenFreebuds, create as create_ofb, OfbEventKind
from openfreebuds.constants import STORAGE_PATH
from openfreebuds.utils.logger import setup_logging, screen_handler, create_logger
from openfreebuds_qt.app.dialog.first_run import OfbQtFirstRunDialog
from openfreebuds_qt.app.main import OfbQtMainWindow
from openfreebuds_qt.config import OfbQtConfigParser, ConfigLock
from openfreebuds_qt.constants import IGNORED_LOG_TAGS, I18N_PATH
from openfreebuds_qt.generic import IOfbQtApplication
from openfreebuds_qt.tray.main import OfbTrayIcon
from openfreebuds_qt.utils import OfbQtDeviceAutoSelect, OfbQtHotkeyService, list_available_locales
from openfreebuds_qt.utils.mpris.service import OfbQtMPRISHelperService
from openfreebuds_qt.utils.updater.service import OfbQtUpdaterService

log = create_logger("OfbQtApplication")


class OfbQtApplication(IOfbQtApplication):
    def __init__(self, args):
        super().__init__(sys.argv)

        self.args = args
        self.tray_available = QSystemTrayIcon.isSystemTrayAvailable()

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
        self.updater_service: Optional[OfbQtUpdaterService] = None

        # Setup logging
        setup_logging(args.verbose)
        if not args.verbose:
            screen_handler.setLevel(logging.ERROR)
        if not args.dont_ignore_logs:
            for tag in IGNORED_LOG_TAGS:
                logging.getLogger(tag).disabled = True

        # App configuration
        ConfigLock.acquire()
        self.config.update_fallback_values(self)

        # Qt base configs
        self.setApplicationName("OpenFreebuds")
        self.setDesktopFileName("pw.mmk.OpenFreebuds")

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

    @staticmethod
    def start(args):
        if (STORAGE_PATH / "force_xorg").is_file():
            print("Enforce xcb Qt backend due to setting")
            os.environ["QT_QPA_PLATFORM"] = "xcb"
        return OfbQtApplication(args).exec_async()

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
            self.updater_service = OfbQtUpdaterService(self.main_window)

            if self.ofb.role == "standalone":
                await self.restore_device()
                await self.auto_select.boot()

            self.hotkeys.start()
            await self.mpris.start()
            await self.tray.boot()
            await self.main_window.boot()
            await self.updater_service.boot()

            # Qt version check & warn
            with suppress(Exception):
                if float(".".join(QT_VERSION_STR.split(".")[:2])) < 6.7:
                    self.show_old_qt_warning()

            # Show UI
            self.tray.show()
            if not self.config.get("ui", "background", True) or self.args.settings:
                self.main_window.show()

            # System tray availability
            if not self.tray_available:
                self.show_no_tray_warning()
                self.main_window.show()
            elif not self.config.get("ui", "first_run_finished", False):
                OfbQtFirstRunDialog(self).show()
        except SystemExit as e:
            self.qt_app.exit(e.args[0])
            ConfigLock.release()
            return
        except Exception:
            log.exception("Boot failure")

    async def exit(self, ret_code: int = 0):
        await self.tray.close()
        self.main_window.hide()

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
                log.debug("Waiting for device connect…")
                await asyncio.sleep(1)

        await self.ofb.run_shortcut(self.args.shortcut)
        self._exit(0)

    async def restore_device(self):
        if self.args.virtual_device:
            return
        name = self.config.get("device", "name", None)
        address = self.config.get('device', "address", None)
        if address is not None:
            log.info(f"Restore device name={name}, address={address}")
            await self.ofb.start(name, address)

    def exec_async(self):
        self.event_loop.create_task(self.boot())
        self.event_loop.run_until_complete(self.close_event.wait())
        self.event_loop.close()

    def show_no_tray_warning(self):
        if self.config.get("warn", "no_tray", False):
            return

        paragraph_1 = self.tr("System tray not available, application won't work in background. "
                              "This will make some features, like global hotkeys, unavailable.")
        paragraph_2 = self.tr("If you're running under GNOME shell, please, check FAQ. "
                              "This warning will be shown only once.")

        QMessageBox(
            QMessageBox.Icon.Warning,
            "OpenFreebuds",
            paragraph_1 + "\n\n" + paragraph_2,
            QMessageBox.StandardButton.Ok,
            self.main_window
        ).show()

        self.config.set("warn", "no_tray", True)
        self.config.save()

    def show_old_qt_warning(self):
        if self.config.get("warn", "old_qt", False):
            return

        paragraph_1 = self.tr(
            "You're running under older version of Qt than expected. "
            "It's strongly recommended to switch to Flatpak release, "
            "because older Qt version may fail your experience of using "
            "OpenFreebuds.")
        paragraph_2 = self.tr("This warning will be shown only once. Please, "
                              "test Flatpak version before reporting bugs.")

        QMessageBox(
            QMessageBox.Icon.Warning,
            "OpenFreebuds",
            paragraph_1 + "\n\n" + paragraph_2,
            QMessageBox.StandardButton.Ok,
            self.main_window
        ).show()

        self.config.set("warn", "old_qt", True)
        self.config.save()
