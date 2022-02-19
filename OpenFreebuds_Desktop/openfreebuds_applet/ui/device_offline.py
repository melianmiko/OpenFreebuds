from pystray import MenuItem

from openfreebuds_applet import icons
from openfreebuds_applet.l18n import t


def process(applet):
    # Set icon if required
    hashsum = "icon_offline"

    if applet.current_icon_hash != hashsum:
        icon = icons.get_icon_offline()
        applet.set_tray_icon(icon, hashsum)

    # Build new menu
    applet.set_menu_items([
        MenuItem(t("mgr_state_" + str(applet.manager.state)),
                 action=None,
                 enabled=False)
    ], expand=True)
