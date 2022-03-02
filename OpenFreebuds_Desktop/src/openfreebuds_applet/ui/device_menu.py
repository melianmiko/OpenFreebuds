from pystray import MenuItem, Menu

from openfreebuds_applet.l18n import t, ln


def process(applet):
    dev = applet.manager.device

    # Build new menu
    if applet.settings.compact_menu:
        applet.set_menu_items([
            *get_power_info(dev),
            Menu.SEPARATOR,
            *get_noise_control_items(dev),
            Menu.SEPARATOR,
            MenuItem(t("submenu_device_config"), Menu(
                *get_gesture_items(dev),
                get_device_lang_menu(dev)
            )),
        ], expand=True)
    else:
        applet.set_menu_items([
            *get_power_info(dev),
            Menu.SEPARATOR,
            *get_noise_control_items(dev),
            Menu.SEPARATOR,
            *get_gesture_items(dev),
            get_device_lang_menu(dev)
        ], expand=True)


def get_device_lang_menu(dev):
    langs = dev.get_property("supported_languages", "").split(",")
    if len(langs) == 0:
        return

    def get_menu_item(lang):
        return MenuItem(ln(lang), lambda: dev.set_property("language", lang))

    sub_items = []
    for a in langs:
        sub_items.append(get_menu_item(a))

    return MenuItem(t("submenu_device_language"), Menu(*sub_items))


def get_power_info(dev):
    items = []
    for n in ["left", "right", "case"]:
        battery = dev.get_property("battery_" + n, 0)
        if battery == 0:
            battery = "--"
        value = t("battery_" + n).format(battery)
        items.append(MenuItem(value,
                              action=None,
                              enabled=False))

    items.append(Menu.SEPARATOR)
    return items


def get_gesture_items(dev):
    items = []

    auto_pause_value = dev.get_property("auto_pause", -1)
    left_2tap = dev.get_property("action_double_tap_left", -99)
    right_2tap = dev.get_property("action_double_tap_right", -99)

    if auto_pause_value != -1:
        items.append(MenuItem(t("gesture_auto_pause"),
                              action=lambda: dev.set_property("auto_pause", not auto_pause_value),
                              checked=lambda _: auto_pause_value))

    if left_2tap != -99:
        items.append(MenuItem(t("double_tap_left"), Menu(
            MenuItem(t("tap_action_off"),
                     action=lambda: dev.set_property("action_double_tap_left", -1),
                     checked=lambda _: left_2tap == -1),
            MenuItem(t("tap_action_pause"),
                     action=lambda: dev.set_property("action_double_tap_left", 1),
                     checked=lambda _: left_2tap == 1),
            MenuItem(t("tap_action_next"),
                     action=lambda: dev.set_property("action_double_tap_left", 2),
                     checked=lambda _: left_2tap == 2),
            MenuItem(t("tap_action_prev"),
                     action=lambda: dev.set_property("action_double_tap_left", 7),
                     checked=lambda _: left_2tap == 7),
            MenuItem(t("tap_action_assistant"),
                     action=lambda: dev.set_property("action_double_tap_left", 0),
                     checked=lambda _: left_2tap == 0)
        )))

    if right_2tap != -99:
        items.append(MenuItem(t("double_tap_right"), Menu(
            MenuItem(t("tap_action_off"),
                     action=lambda: dev.set_property("action_double_tap_right", -1),
                     checked=lambda _: right_2tap == -1),
            MenuItem(t("tap_action_pause"),
                     action=lambda: dev.set_property("action_double_tap_right", 1),
                     checked=lambda _: right_2tap == 1),
            MenuItem(t("tap_action_next"),
                     action=lambda: dev.set_property("action_double_tap_right", 2),
                     checked=lambda _: right_2tap == 2),
            MenuItem(t("tap_action_prev"),
                     action=lambda: dev.set_property("action_double_tap_right", 7),
                     checked=lambda _: right_2tap == 7),
            MenuItem(t("tap_action_assistant"),
                     action=lambda: dev.set_property("action_double_tap_right", 0),
                     checked=lambda _: right_2tap == 0)
        )))

    return items


def get_noise_control_items(dev):
    current = dev.get_property("noise_mode", -1)
    next_mode = (current + 1) % 3

    if current == -1:
        return []

    return [
        MenuItem(t("noise_mode_0"),
                 action=lambda: dev.set_property("noise_mode", 0),
                 checked=lambda _: current == 0,
                 default=lambda _: next_mode == 0),
        MenuItem(t("noise_mode_1"),
                 action=lambda: dev.set_property("noise_mode", 1),
                 checked=lambda _: current == 1,
                 default=lambda _: next_mode == 1),
        MenuItem(t("noise_mode_2"),
                 action=lambda: dev.set_property("noise_mode", 2),
                 checked=lambda _: current == 2,
                 default=lambda _: next_mode == 2)
    ]

