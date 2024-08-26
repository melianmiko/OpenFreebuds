import asyncio
import sys
from typing import Optional

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.helper.setting_tab_helper import OfbQtSettingsTabHelper
from openfreebuds_qt.app.module.choose_device import OfbQtChooseDeviceModule
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.app.module.device_info import OfbQtDeviceInfoModule
from openfreebuds_qt.app.module.dual_connect import OfbQtDualConnectModule
from openfreebuds_qt.app.module.empty_module import OfbEmptyModule
from openfreebuds_qt.app.module.gestures import OfbQtGesturesModule
from openfreebuds_qt.app.module.sound_quality import OfbQtSoundQualityModule

log = create_logger("OfbQtSettingsUi")


class OfbQtSettingsUi:
    def __init__(self, tabs_helper: OfbQtSettingsTabHelper, ofb: IOpenFreebuds):
        self.tabs = tabs_helper
        self.ofb = ofb
        self._ui_update_task: Optional[asyncio.Task] = None
        self._ui_modules: list[OfbQtCommonModule] = []

        # App-related modules
        self._attach_module("About Openfreebuds...", OfbEmptyModule(self.tabs.root))
        self._attach_module("User interface", OfbEmptyModule(self.tabs.root))
        if self.ofb.role == "standalone":
            self._attach_module("Select device", OfbQtChooseDeviceModule(self.tabs.root, self.ofb))

        # Device-related modules
        self.device_section = self.tabs.add_section("Device-related")
        self._attach_module("Device info", OfbQtDeviceInfoModule(self.tabs.root, self.ofb))
        self._attach_module("Dual-connect", OfbQtDualConnectModule(self.tabs.root, self.ofb))
        self._attach_module("Gestures", OfbQtGesturesModule(self.tabs.root, self.ofb))
        self._attach_module("Sound quality", OfbQtSoundQualityModule(self.tabs.root, self.ofb))
        self._attach_module("Other settings", OfbEmptyModule(self.tabs.root))

        # Addon-related modules
        self.tabs.add_section("Extras")
        self._attach_module("Keyboard shortcuts", OfbEmptyModule(self.tabs.root))
        if sys.platform == "linux":
            self._attach_module("Linux-related", OfbEmptyModule(self.tabs.root))

        self.tabs.finalize_list()

    def on_show(self):
        self._ui_update_task = asyncio.create_task(self._update_loop())

    def on_hide(self):
        if self._ui_update_task is not None:
            self._ui_update_task.cancel()

    def retranslate_ui(self):
        self.tabs.retranslate_ui()

    def _attach_module(self, label: str, module: OfbQtCommonModule):
        entry = self.tabs.add_tab(label, module)
        self._ui_modules.append(module)
        module.list_item = entry.list_item

    async def boot(self):
        await self._update_ui(OfbCoreEvent(None))

    async def _update_ui(self, event: OfbCoreEvent):
        if event.kind_match(OfbEventKind.DEVICE_CHANGED):
            device_name, _ = await self.ofb.get_device_tags()
            self.device_section.list_item.setText(device_name)

        if event.kind_match(OfbEventKind.STATE_CHANGED):
            visible = await self.ofb.get_state() == IOpenFreebuds.STATE_CONNECTED
            self._device_section_set_visible(visible)

        for mod in self._ui_modules:
            try:
                await mod.update_ui(event)
            except Exception:
                log.exception(f"Failed to update UI {mod}")

    async def _update_loop(self):
        """
        Background task that will subscribe to core event bus and watch
        for changes to perform settings UI update
        """

        member_id = await self.ofb.subscribe()
        log.info(f"Settings UI update loop started, member_id={member_id}")

        try:
            while True:
                kind, *args = await self.ofb.wait_for_event(member_id)
                await self._update_ui(OfbCoreEvent(kind, *args))
        except asyncio.CancelledError:
            await self.ofb.unsubscribe(member_id)
            log.info("Settings UI update loop finished")

    def _device_section_set_visible(self, visible):
        self.device_section.set_visible(visible)
        if not visible and self.tabs.active_tab.section == self.device_section:
            self.tabs.set_active_tab(0, 0)
