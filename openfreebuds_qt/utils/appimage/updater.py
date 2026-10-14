"""
In-place updates for the AppImage build, from the latest GitHub release.
"""
import hashlib
import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import aiohttp
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QWidget

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.utils.appimage.integration import relaunch
from openfreebuds_qt.utils.qt_utils import exec_msg_box_async

log = create_logger("OfbAppImageUpdater")

GITHUB_API = "https://api.github.com"
HTTP_HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "OpenFreebuds"}


@dataclass(frozen=True)
class AppImageRelease:
    version: str
    url: str
    page: str
    sha256: Optional[str] = None
    checksum_url: Optional[str] = None


def version_key(version: str) -> tuple[int, ...]:
    """Numeric version parts, so that 0.18.1.1 > 0.18.1 and 0.18.10 > 0.18.9"""
    match = re.match(r"v?(\d+(?:\.\d+)*)", version)
    if match is None:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def pick_release(data: dict, arch: str) -> Optional[AppImageRelease]:
    """Find the AppImage of the given architecture in a GitHub release"""
    assets = {asset["name"]: asset for asset in data.get("assets", [])}
    for name, asset in assets.items():
        if not name.endswith(f"-{arch}.AppImage"):
            continue
        digest = asset.get("digest") or ""
        checksum = assets.get(f"{name}.sha256")
        return AppImageRelease(
            version=data["tag_name"].removeprefix("v"),
            url=asset["browser_download_url"],
            page=data.get("html_url", ""),
            sha256=digest.removeprefix("sha256:") if digest.startswith("sha256:") else None,
            checksum_url=checksum["browser_download_url"] if checksum else None,
        )
    return None


class OfbAppImageUpdater:
    """
    Replaces the running AppImage with the latest release.
    Provides the part of the mmk_updater API used by the UI.
    """

    def __init__(self, parent: QWidget, repo: str, current_version: str, app_path: Path):
        self.parent = parent
        self.repo = repo
        self.current_version = current_version
        self.app_path = app_path
        self.config = SimpleNamespace(app_display_name="OpenFreebuds")
        self.release_info: Optional[AppImageRelease] = None
        self.has_update = False

    async def boot(self):
        try:
            await self.check_now(False)
        except Exception:
            log.exception("Update check failed")

    async def check_now(self, interactive: bool):
        async with aiohttp.ClientSession(headers=HTTP_HEADERS) as session:
            async with session.get(f"{GITHUB_API}/repos/{self.repo}/releases/latest") as resp:
                resp.raise_for_status()
                data = await resp.json()

        self.release_info = pick_release(data, platform.machine())
        self.has_update = (self.release_info is not None
                           and version_key(self.release_info.version) > version_key(self.current_version))
        log.info(f"Latest release {data.get('tag_name')}, has_update={self.has_update}")

        update_view = getattr(self.parent, "update_view", None)
        if update_view is not None:
            update_view.update_widget()
        if not interactive:
            return

        if not self.has_update:
            await self._message(QMessageBox.Icon.Information,
                                QApplication.translate("OfbAppImageUpdater", "You're using the latest version."))
            return

        text = QApplication.translate("OfbAppImageUpdater", "Version {} is available. Download and install it now?")
        if await self._message(QMessageBox.Icon.Question, text.format(self.release_info.version), ask=True):
            await self.install(self.release_info)

    async def install(self, release: AppImageRelease):
        part = self.app_path.with_name(f".{self.app_path.name}.part")
        progress = QProgressDialog(QApplication.translate("OfbAppImageUpdater", "Downloading update…"),
                                   None, 0, 100, self.parent)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        try:
            async with aiohttp.ClientSession(headers=HTTP_HEADERS) as session:
                expected = release.sha256 or await self._fetch_checksum(session, release)
                if not expected:
                    raise RuntimeError("Release has no checksum")

                digest = hashlib.sha256()
                async with session.get(release.url) as resp:
                    resp.raise_for_status()
                    total = resp.content_length or 0
                    done = 0
                    with open(part, "wb") as f:
                        async for chunk in resp.content.iter_chunked(1 << 16):
                            f.write(chunk)
                            digest.update(chunk)
                            done += len(chunk)
                            if total:
                                progress.setValue(int(done * 100 / total))

            if digest.hexdigest() != expected.lower():
                raise RuntimeError("Downloaded file checksum mismatch")
            part.chmod(0o755)
            os.replace(part, self.app_path)
        except Exception as e:
            part.unlink(missing_ok=True)
            log.exception("Update failed")
            progress.close()
            await self._message(QMessageBox.Icon.Critical,
                                QApplication.translate("OfbAppImageUpdater", "Update failed: {}").format(e))
            return

        progress.close()
        text = QApplication.translate("OfbAppImageUpdater", "Update installed. Restart OpenFreebuds now?")
        if await self._message(QMessageBox.Icon.Information, text, ask=True):
            await self.restart()

    async def restart(self):
        relaunch(self.app_path)
        await self.parent.ctx.exit()

    async def _message(self, icon: QMessageBox.Icon, text: str, ask: bool = False) -> bool:
        buttons = (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                   if ask else QMessageBox.StandardButton.Ok)
        box = QMessageBox(icon, "OpenFreebuds", text, buttons, self.parent)
        return await exec_msg_box_async(box) == QMessageBox.StandardButton.Yes

    @staticmethod
    async def _fetch_checksum(session: aiohttp.ClientSession, release: AppImageRelease) -> Optional[str]:
        if release.checksum_url is None:
            return None
        async with session.get(release.checksum_url) as resp:
            resp.raise_for_status()
            return (await resp.text()).split()[0]
