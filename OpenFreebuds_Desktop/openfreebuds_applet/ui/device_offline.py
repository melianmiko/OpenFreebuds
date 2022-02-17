from pystray import MenuItem
from openfreebuds_applet.l18n import t


def loop(applet):
    # TODO: Set icon...

    # Build new menu
    applet.set_menu_items([
        MenuItem(t("mgr_state_" + str(applet.manager.state)),
                 action=None,
                 enabled=False)
    ], expand=True)

    applet.manager.state_changed.clear()
    applet.manager.state_changed.wait()
