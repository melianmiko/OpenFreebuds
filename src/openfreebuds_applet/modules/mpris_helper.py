import logging

from mpris import MediaPlayer2
from openfreebuds import event_bus
from openfreebuds.constants.events import EVENT_DEVICE_PROP_CHANGED
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet import utils

log = logging.getLogger("MprisHelper")

class _Config:
    applet = None
    started = False
    paused_players = []


def start(applet):
    _Config.applet = applet

    if applet.settings.enable_mpris_helper and not _Config.started:
        _mpris_thread()


def should_handle_in_ear():
    applet = _Config.applet

    auto_pause_enabled = False
    if applet.manager.device:
        auto_pause_enabled = applet.manager.device.find_property("config", "auto_pause", 0) > 0

    return applet.settings.enable_mpris_helper and auto_pause_enabled


def pause_all_players():
    _Config.paused_players = []
    for player, dbus_path in MediaPlayer2.get_all():
        if player.playback_status == "Playing":
            log.info(f"Pause {player.identity} media player")
            player.pause()
            _Config.paused_players.append(dbus_path)


def resume_players():
    for dbus_path in _Config.paused_players:
        player = MediaPlayer2(dbus_path)
        log.info(f"Resume previously paused {player.identity}")
        player.play()
    _Config.paused_players = []


@utils.async_with_ui("MprisHelperThread")
def _mpris_thread():
    event = event_bus.register([
        EVENT_DEVICE_PROP_CHANGED
    ])

    log.info("Started!")

    manager = _Config.applet.manager    # type: FreebudsManager

    last_in_ear = False
    if manager.device:
        last_in_ear = manager.device.find_property("state", "in_ear", False)

    while True:
        # If feature is disabled, do nothing and exit
        if not _Config.applet.settings.enable_mpris_helper:
            log.info("Exited!")
            _Config.started = False
            return

        # Get new in-ear status
        in_ear = False
        if manager.device:
            in_ear = manager.device.find_property("state", "in_ear", False)

        # Handle in-ear state change
        if in_ear != last_in_ear and should_handle_in_ear():
            log.info(f"{last_in_ear} {in_ear}")

            if last_in_ear is True and in_ear is False:
                pause_all_players()
            elif last_in_ear is False and in_ear is True:
                resume_players()

            last_in_ear = in_ear

        event.wait()
