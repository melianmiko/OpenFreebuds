import asyncio
import os
import sys
from typing import Optional

from openfreebuds import IOpenFreebuds, OfbEventKind
from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.app.helper.core_event import OfbCoreEvent
from openfreebuds_qt.app.helper.setting_tab_helper import OfbQtSettingsTabHelper
from openfreebuds_qt.app.module.about import OfbQtAboutModule
from openfreebuds_qt.app.module.choose_device import OfbQtChooseDeviceModule
from openfreebuds_qt.app.module.common import OfbQtCommonModule
from openfreebuds_qt.app.module.device_info import OfbQtDeviceInfoModule
from openfreebuds_qt.app.module.device_other import OfbQtDeviceOtherSettingsModule
from openfreebuds_qt.app.module.dual_connect import OfbQtDualConnectModule
from openfreebuds_qt.app.module.empty_module import OfbEmptyModule
from openfreebuds_qt.app.module.gestures import OfbQtGesturesModule
from openfreebuds_qt.app.module.hotkeys_module import OfbQtHotkeysModule
from openfreebuds_qt.app.module.linux_related import OfbQtLinuxExtrasModule
from openfreebuds_qt.app.module.sound_quality import OfbQtSoundQualityModule
from openfreebuds_qt.app.qt_utils import qt_error_handler
from openfreebuds_qt.generic import IOfbQtContext

log = create_logger("OfbQtSettingsUi")


class OfbQtSettingsUi:
    def __init__(self, tabs_helper: OfbQtSettingsTabHelper, context: IOfbQtContext):
        self.tabs = tabs_helper
        self.ctx = context
        self.ofb = context.ofb
        self._ui_update_task: Optional[asyncio.Task] = None
        self._ui_modules: list[OfbQtCommonModule] = []

        # App-related modules
        self._attach_module("About Openfreebuds...", OfbQtAboutModule(self.tabs.root, self.ctx))
        self._attach_module("User interface", OfbEmptyModule(self.tabs.root, self.ctx))
        if self.ctx.ofb.role == "standalone":
            self._attach_module("Select device", OfbQtChooseDeviceModule(self.tabs.root, self.ctx))
        if OfbQtHotkeysModule.available():
            self._attach_module("Keyboard shortcuts", OfbQtHotkeysModule(self.tabs.root, self.ctx))
        if sys.platform == "linux":
            self._attach_module("Linux-related", OfbQtLinuxExtrasModule(self.tabs.root, self.ctx))

        # Device-related modules
        self.device_section = self.tabs.add_section("Device-related")
        self._attach_module("Device info", OfbQtDeviceInfoModule(self.tabs.root, self.ctx))
        self._attach_module("Dual-connect", OfbQtDualConnectModule(self.tabs.root, self.ctx))
        self._attach_module("Gestures", OfbQtGesturesModule(self.tabs.root, self.ctx))
        self._attach_module("Sound quality", OfbQtSoundQualityModule(self.tabs.root, self.ctx))
        self._attach_module("Other settings", OfbQtDeviceOtherSettingsModule(self.tabs.root, self.ctx))

        # Finish
        self.default_tab = 0, 1
        self.tabs.finalize_list()
        self.tabs.set_active_tab(*self.default_tab)

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

        async with qt_error_handler("OfbQtSettings_UpdateLoop", self.ctx):
            member_id = await self.ctx.ofb.subscribe()
            log.info(f"Settings UI update loop started, member_id={member_id}")

            # First-time force update everything
            await self._update_ui(OfbCoreEvent(None))

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
            self.tabs.set_active_tab(*self.default_tab)
