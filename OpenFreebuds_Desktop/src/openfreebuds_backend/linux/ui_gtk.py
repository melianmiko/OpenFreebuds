import logging
import gi

gi.require_version("Gtk", "3.0")

log = logging.getLogger("LinuxBackend")


def ask_string(message, callback):
    from gi.repository import GLib, Gtk

    def show_async():
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


def ui_lock():
    from gi.repository import Gtk
    Gtk.main()


def is_dark_theme():
    from gi.repository import Gtk
    settings = Gtk.Settings()
    defaults = settings.get_default()
    theme_name = defaults.get_property("gtk-theme-name")
    return "Dark" in theme_name
