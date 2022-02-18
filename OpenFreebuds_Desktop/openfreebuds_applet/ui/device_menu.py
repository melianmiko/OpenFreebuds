from pystray import MenuItem, Menu

from openfreebuds_applet.l18n import t


def loop(applet):
    while applet.manager.state == applet.manager.STATE_CONNECTED:
        applet.manager.device.on_property_change.clear()
        update(applet)

        applet.manager.device.on_property_change.wait()


def update(applet):
    dev = applet.manager.device

    # TODO: Set icon...

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
