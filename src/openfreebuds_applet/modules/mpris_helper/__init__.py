import logging
import tkinter

from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_DEVICE_PROP_CHANGED
from openfreebuds.logger import create_log
from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules.generic import GenericModule
from .mpris import MediaPlayer2

log = create_log("MprisHelper")


class Module(GenericModule):
    ident = "mpris_helper"
    name = t("option_mpris_helper")
    description = t("option_mpris_helper_guide")

    os_filter = ["linux"]
    def_settings = {
        "enabled": False
    }

    def __init__(self):
        super().__init__()
        self.paused_players = []

    def should_handle_in_ear(self):
        auto_pause_enabled = False
        if self.app_manager.device:
            auto_pause_enabled = self.app_manager.device.find_property("config", "auto_pause", 0) > 0
        return auto_pause_enabled

    def pause_all(self):
        self.paused_players = []
        for player, dbus_path in MediaPlayer2.get_all():
            if player.playback_status == "Playing":
                log.info(f"Pause {player.identity} media player")
                player.pause()
                self.paused_players.append(dbus_path)

    def resume_all(self):
        for dbus_path in self.paused_players:
            player = MediaPlayer2(dbus_path)
            log.info(f"Resume previously paused {player.identity}")
            player.play()
        self.paused_players = []

    def _mainloop(self):
        event = event_bus.register([
            EVENT_DEVICE_PROP_CHANGED
        ])

        last_in_ear = False
        if self.app_manager.device:
            last_in_ear = self.app_manager.device.find_property("state", "in_ear", False)

        while self.running:
            # Get new in-ear status
            in_ear = False
            if self.app_manager.device:
                in_ear = self.app_manager.device.find_property("state", "in_ear", False)

            # Handle in-ear state change
            if in_ear != last_in_ear and self.should_handle_in_ear():
                log.info(f"{last_in_ear} {in_ear}")

                if last_in_ear is True and in_ear is False:
                    self.pause_all()
                elif last_in_ear is False and in_ear is True:
                    self.resume_all()

                last_in_ear = in_ear

            event.wait()
