from pystray import MenuItem, Menu

from openfreebuds_applet.l18n import t


def process(applet):
    dev = applet.manager.device

    # Build new menu
    items = []
    add_power_info(dev, items)
    add_noise_control(dev, items)
    items.append(Menu.SEPARATOR)
    add_gestures_menu(dev, items)
    add_device_language_menu(dev, items)

    applet.set_menu_items(items, expand=True)


def add_device_language_menu(dev, items):
    langs = dev.get_property("supported_languages", "").split(",")
    if len(langs) == 0:
        return

    def get_menu_item(lang):
        return MenuItem(lang, lambda: dev.set_property("language", lang))

    sub_items = []
    for a in langs:
        sub_items.append(get_menu_item(a))

    items.append(MenuItem(t("submenu_device_language"), Menu(*sub_items)))


def add_power_info(dev, items):
    for n in ["left", "right", "case"]:
        battery = dev.get_property("battery_" + n, 0)
        if battery == 0:
            battery = "--"
        value = t("battery_" + n).format(battery)
        items.append(MenuItem(value,
                              action=None,
                              enabled=False))

    items.append(Menu.SEPARATOR)


def add_gestures_menu(dev, items):
    submenu_items = []

    auto_pause_value = dev.get_property("auto_pause", -1)
    left_2tap = dev.get_property("action_double_tap_left", -99)
    right_2tap = dev.get_property("action_double_tap_right", -99)

    if auto_pause_value != -1:
        submenu_items.extend([
            MenuItem(t("gesture_auto_pause"),
                     action=lambda: dev.set_property("auto_pause", not auto_pause_value),
                     checked=lambda _: auto_pause_value),
            Menu.SEPARATOR
        ])

    if left_2tap != -99:
        section_items = [
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
        ]
        submenu_items.append(MenuItem(t("double_tap_left"), Menu(*section_items)))

    if right_2tap != -99:
        section_items = [
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
        ]
        submenu_items.append(MenuItem(t("double_tap_right"), Menu(*section_items)))

    items.append(MenuItem(t("submenu_gestures"), action=Menu(*submenu_items)))


def add_noise_control(dev, items):
    current = dev.get_property("noise_mode", -1)

    if current == -1:
        return

    next_mode = (current + 1) % 3

    items.append(MenuItem(t("noise_mode_0"),
                          action=lambda: dev.set_property("noise_mode", 0),
                          checked=lambda _: current == 0,
                          default=lambda _: next_mode == 0))
    items.append(MenuItem(t("noise_mode_1"),
                          action=lambda: dev.set_property("noise_mode", 1),
                          checked=lambda _: current == 1,
                          default=lambda _: next_mode == 1))
    items.append(MenuItem(t("noise_mode_2"),
                          action=lambda: dev.set_property("noise_mode", 2),
                          checked=lambda _: current == 2,
                          default=lambda _: next_mode == 2))
