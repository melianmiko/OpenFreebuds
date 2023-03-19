from pystray import Menu as BaseMenu, MenuItem


class Menu(BaseMenu):
    def __init__(self, *items):
        super().__init__(*items)
        self._items = []
        self._static_items = list(items)

    @property
    def items(self):
        self._items = []
        self.on_build()
        return self._items

    def on_build(self):
        # Override to generate menu dynamically
        self._items = self._static_items

    def add_item(self, text, action=None, checked=None, enabled=True, visible=True, default=False, args=()):
        if not visible:
            return

        if not isinstance(text, str):
            raise Exception("Must be string")

        item = MenuItem(text,
                        action=lambda: action(*args),
                        checked=lambda _: checked,
                        default=default,
                        enabled=enabled)
        self._items.append(item)

    def include(self, menu, visible=True):
        if not visible:
            return

        self._items += menu.items

    def add_submenu(self, text: str, menu, visible=True):
        if not visible:
            return

        item = MenuItem(text, menu)
        self._items.append(item)

    def add_separator(self):
        self._items.append(self.SEPARATOR)

    def wrap(self, text):
        # Convert all added content to one submenu
        menu = MenuItem(text, Menu(*self._items))
        self._items = [menu]
