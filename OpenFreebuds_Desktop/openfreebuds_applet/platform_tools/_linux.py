import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

RESULT_YES = -8
RESULT_NO = -9


# noinspection PyArgumentList
def show_message(message, window_title=""):
    msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO,
                            Gtk.ButtonsType.OK, window_title)
    msg.format_secondary_text(message)
    msg.run()
    msg.close()


# noinspection PyArgumentList
def show_question(message, window_title=""):
    msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO,
                            Gtk.ButtonsType.YES_NO, window_title)
    msg.format_secondary_text(message)
    result = msg.run()
    msg.close()

    return result


def is_dark_theme():
    settings = Gtk.Settings.get_default()
    theme_name = settings.get_property("gtk-theme-name")
    return "Dark" in theme_name
