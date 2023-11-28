class MediaPlayer2:
    @staticmethod
    def get_all():
        import dbus
        bus = dbus.SessionBus()

        output = []
        for path in bus.list_names():
            if str(path).startswith("org.mpris.MediaPlayer2"):
                output.append((MediaPlayer2(path), path))
        return output

    def __init__(self, path):
        import dbus
        bus = dbus.SessionBus()

        self._obj = bus.get_object(path, "/org/mpris/MediaPlayer2")
        self._props = dbus.Interface(self._obj, "org.freedesktop.DBus.Properties")
        self._player = dbus.Interface(self._obj, "org.mpris.MediaPlayer2.Player")

    @property
    def identity(self):
        return self._props.Get("org.mpris.MediaPlayer2", "Identity")

    @property
    def playback_status(self):
        return self._props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")

    def pause(self):
        return self._player.Pause()

    def play(self):
        return self._player.Play()
