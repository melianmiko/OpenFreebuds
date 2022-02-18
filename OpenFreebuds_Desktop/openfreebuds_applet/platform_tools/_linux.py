import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

RESULT_YES = -5
RESULT_NO = -6


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
                            Gtk.ButtonsType.OK_CANCEL, window_title)
    msg.format_secondary_text(message)
    result = msg.run()
    msg.close()

    return result

