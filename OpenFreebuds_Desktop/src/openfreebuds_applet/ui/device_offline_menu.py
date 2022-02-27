from pystray import MenuItem

from openfreebuds_applet.l18n import t


def process(applet):
    # Build new menu
    applet.set_menu_items([
        MenuItem(t("mgr_state_" + str(applet.manager.state)),
                 action=None,
                 enabled=False)
    ], expand=True)
