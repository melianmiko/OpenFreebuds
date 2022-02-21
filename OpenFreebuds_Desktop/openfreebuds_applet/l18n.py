STRINGS = {
    "first_run_title": "Welcome to OpenFreebuds",
    "first_run_message": "This app don't have any window, it "
                         "displays only in system tray.\n\n"
                         "Right click on headset icon in tray to set up.",
    "no_menu_error_title": "App don't work",
    "no_menu_error_info": "We can't create tray icon and/or menu on your OS. "
                          "If you're using Linux, please check that libappindicator "
                          "and other dependencies are installed.\n\n"
                          "Open OpenFreebuds webpage for more information?",
    "application_running_message": "Application already running, check your taskbar status area.\n\n "
                                   "If them don't response, stop it from system task manager, \n"
                                   "and then try to launch again.",
    "select_device": "Select one of paired devices:",
    "action_open_appdata": "Open app data directory",
    "action_exit": "Exit application",
    "submenu_theme": "Icon style",
    "submenu_device_info": "Device info",
    "submenu_gestures": "Gestures",
    "submenu_hotkeys": "Global hotkeys",
    "gesture_auto_pause": "Pause on remove",
    "double_tap_left": "Double-tap on left",
    "double_tap_right": "Double-tap on right",
    "tap_action_off": "Disabled",
    "tap_action_pause": "Play/pause",
    "tap_action_next": "Next track",
    "tap_action_prev": "Prev track",
    "tap_action_assistant": "Voice assistant",
    "theme_auto": "Auto-detect",
    "theme_light": "Light icon",
    "theme_dark": "Dark icon",
    "action_unpair": "Forgot device",
    "state_quiting": "Stopping...",
    "action_kill_app": "Force exit",
    "action_refresh_list": "Refresh list",
    "mgr_state_0": "No device",
    "mgr_state_1": "Device don't connected",
    "mgr_state_2": "Device disconnected",
    "mgr_state_3": "Connecting...",
    "mgr_state_4": "Connected",
    "mgr_state_5": "Failed to connect",
    "battery_left": "Left headphone: {}%",
    "battery_right": "Right headphone: {}%",
    "battery_case": "Case headphone: {}%",
    "noise_mode_0": 'Off',
    "noise_mode_1": "Noise cancellation",
    "noise_mode_2": "Awareness",
    "hotkeys_wayland": "Global hotkeys won't work correctly under Wayland.\n\n"
                       "We can't fix it for now. But you can use HTTP-controller to "
                       "create this hotkeys by yourself, more info about this will be "
                       "available later",
    "notice_restart": "Restart app to apply this settings",
    "prop_enabled": "Enabled",
    "hotkey_next_mode": "Switch noise mode"
}


def t(prop):
    return STRINGS[prop]
