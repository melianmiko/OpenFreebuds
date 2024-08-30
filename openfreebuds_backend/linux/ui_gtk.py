import gi

from openfreebuds.utils.logger import create_logger

gi.require_version("Gtk", "3.0")

log = create_logger("LinuxBackend")


# noinspection PyPackageRequirements
def ask_string(message, callback):
    from gi.repository import GLib, Gtk

    # noinspection PyArgumentList,PyUnresolvedReferences
    def show_async():
        # noinspection PyTypeChecker
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK_CANCEL, "OpenFreebuds")
        dialog.format_secondary_text(message)

        area = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_margin_start(16)
        entry.set_margin_end(16)
        area.pack_end(entry, False, False, 0)
        dialog.show_all()

        response = dialog.run()
        text = entry.get_text()
        dialog.destroy()

        if response != Gtk.ResponseType.OK:
            text = None

        callback(text)

    GLib.idle_add(show_async)


def is_dark_taskbar():
    from gi.repository import Gtk
    settings = Gtk.Settings()
    defaults = settings.get_default()
    theme_name = defaults.get_property("gtk-theme-name")
    log.info(f"System theme name is {theme_name}")
    return "Dark" in theme_name
