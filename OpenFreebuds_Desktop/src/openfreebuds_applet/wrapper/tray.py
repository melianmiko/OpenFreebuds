import pystray


class TrayMenu:
    def __init__(self):
        self.contents = []

    def on_build(self):
        pass

    def add_item(self, text, action=None, checked=None, enabled=True, visible=True, default=False, args=()):
        if not visible:
            return

        if not isinstance(text, str):
            raise Exception("Must be string")

        item = pystray.MenuItem(text,
                                action=lambda: action(*args),
                                checked=lambda _: checked,
                                default=default,
                                enabled=enabled)
        self.contents.append(item)

    def include(self, menu, visible=True):
        if not visible:
            return

        items = menu.build()
        self.contents += items

    def add_submenu(self, text, menu, visible=True):
        if not visible:
            return

        item = pystray.MenuItem(text, pystray.Menu(*menu.build()))
        self.contents.append(item)

    def add_separator(self):
        self.contents.append(pystray.Menu.SEPARATOR)

    def wrap(self, text):
        # Convert all added content to one submenu
        menu = pystray.MenuItem(text, pystray.Menu(*self.contents))
        self.contents = [menu]

    def build(self):
        self.contents = []
        self.on_build()
        return self.contents
