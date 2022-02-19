from pystray import MenuItem, Menu

from openfreebuds_applet import icons
from openfreebuds_applet.l18n import t


def process(applet):
    dev = applet.manager.device

    # Set icon if required
    battery_left = dev.get_property("battery_left")
    battery_right = dev.get_property("battery_right")
    battery_min = min(battery_right, battery_left)
    noise_mode = dev.get_property("noise_mode")
    hashsum = "device_" + str(battery_min) + "_" + str(noise_mode)

    if applet.current_icon_hash != hashsum:
        icon = icons.get_icon_device(battery_min, noise_mode)
        applet.set_tray_icon(icon, hashsum)

    # Build new menu
    items = []
    add_power_info(dev, items)
    add_noise_control(dev, items)

    applet.set_menu_items(items, expand=True)


def add_power_info(dev, items):
    for n in ["left", "right", "case"]:
        value = t("battery_" + n).format(dev.get_property("battery_" + n, "--"))
        items.append(MenuItem(value,
                              action=None,
                              enabled=False))

    items.append(Menu.SEPARATOR)


def add_noise_control(dev, items):
    for n in [1, 0, 2]:
        items.append(mk_noise_action(dev, n))


def mk_noise_action(dev, n):
    return MenuItem(t("noise_mode_" + str(n)),
                    checked=lambda item: (dev.get_property("noise_mode", -1) == n),
                    action=lambda: dev.set_property("noise_mode", n))
