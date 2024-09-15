import logging


log = logging.getLogger("OfbLinuxBackend")


def is_dark_taskbar():
    try:
        import gi
        gi.require_version("Gtk", "3.0")

        from gi.repository import Gtk
        settings = Gtk.Settings()
        defaults = settings.get_default()
        theme_name = defaults.get_property("gtk-theme-name")
        log.info(f"System theme name is {theme_name}")
        return "Dark" in theme_name
    except ImportError:
        return False
