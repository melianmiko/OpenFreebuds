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
    "select_device": "Select device to use:",
    "action_exit": "Exit",
    "action_unpair": "Forgot device",
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
    "noise_mode_2": "Awareness"
}


def t(prop):
    return STRINGS[prop]
