import sys

from PyQt6.QtWidgets import QWidget

from openfreebuds.constants import STORAGE_PATH
from openfreebuds.utils.logger import create_logger
from openfreebuds_backend import AUTOUPDATE_AVAILABLE
from openfreebuds_qt.config import OfbQtConfigParser
from openfreebuds_qt.version_info import VERSION

try:
    from mmk_updater import UpdateCheckerConfig
    from mmk_updater.qt import MmkUpdaterQt
except ImportError:
    UpdateCheckerConfig = None
    MmkUpdaterQt = None

log = create_logger("OfbQtUpdaterService")


def _is_remote_newer(current: str, remote: str) -> bool:
    """
    Return True only when the remote version is strictly newer than the
    currently installed one. The bundled mmk_updater compares versions with a
    plain ``!=``, so a fork build whose version is *higher* than the upstream
    release still gets flagged as "update available". Use a proper semantic
    comparison and fall back to the conservative behaviour (notify only on a
    real difference where remote sorts after current) when parsing fails.
    """
    if not remote:
        return False
    try:
        from packaging.version import InvalidVersion, parse

        try:
            return parse(remote) > parse(current)
        except InvalidVersion:
            pass
    except ImportError:
        pass

    # Fallback when versions can't be parsed semantically: be conservative and
    # only notify when the remote string differs and sorts strictly after the
    # current one. Never offer an update for an unreadable/equal version.
    try:
        return bool(remote) and remote != current and remote > current and remote[0].isdigit()
    except Exception:  # noqa: BLE001 - never raise from a version check
        return False


if MmkUpdaterQt is not None:

    class OfbSafeUpdaterQt(MmkUpdaterQt):
        """mmk_updater that never offers a downgrade or a same-version update."""

        def __init__(self, parent, config):
            super().__init__(parent, config)
            self._user_triggered = False

        @property
        def has_update(self):
            if self.release_info is None:
                return False
            return _is_remote_newer(self.config.current_version, self.release_info.version)

        async def check_now(self, user_triggered: bool = False):
            self._user_triggered = user_triggered
            await super().check_now(user_triggered)

        async def show_update_confirm(self) -> bool:
            if self.release_info is not None and not _is_remote_newer(
                self.config.current_version, self.release_info.version
            ):
                log.debug("Remote version is not newer, skip update prompt")
                if self._user_triggered:
                    try:
                        from mmk_updater.i18n import t

                        await self.show_dialog_message(t("You're using latest version"))
                    except Exception:  # noqa: BLE001 - best-effort notice only
                        pass
                return False
            return await super().show_update_confirm()
else:
    OfbSafeUpdaterQt = None


class OfbQtUpdaterService:
    def __init__(self, parent: QWidget):
        self.config = OfbQtConfigParser.get_instance()

        is_win32 = sys.platform == "win32"
        mode = self.config.get("updater", "mode", "show")

        if UpdateCheckerConfig is not None and MmkUpdaterQt is not None:
            self.updater_config = UpdateCheckerConfig(
                server_url="https://st.mmk.pw/openfreebuds",
                current_version=VERSION,
                state_location=STORAGE_PATH / "qt_updater.json",
                app_display_name="OpenFreebuds",
                notify_method=(UpdateCheckerConfig.NotifyMethod.POP_UP
                               if is_win32 and mode == "show"
                               else UpdateCheckerConfig.NotifyMethod.NONE)
            )
            self.updater = OfbSafeUpdaterQt(parent, self.updater_config)    # type: MmkUpdaterQt
        else:
            self.updater_config = None
            self.updater = None                                         # type: MmkUpdaterQt

    async def boot(self):
        if UpdateCheckerConfig is None:
            log.info("Skip, unavailable")
            return

        if self.config.get("updater", "mode", "show") == "off":
            return

        if "git" in VERSION or not AUTOUPDATE_AVAILABLE:
            return

        await self.updater.boot()

    async def check_now(self):
        await self.updater.check_now(True)
