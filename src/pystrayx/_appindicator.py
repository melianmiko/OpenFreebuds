from pystray._appindicator import Icon as ParentIcon
from pystray._util import notify_dbus


class Icon(ParentIcon):
    def _initialize(self):
        self._notifier = notify_dbus.Notifier()
        self._mark_ready()
