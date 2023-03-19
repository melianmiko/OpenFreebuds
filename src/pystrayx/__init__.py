import sys

from . import _menu


def backend():
    if sys.platform == "win32":
        from pystray import _win32
        return _win32
    else:
        from . import _appindicator
        return _appindicator


TrayApplication = backend().Icon
Menu = _menu.Menu
MenuItem = _menu.MenuItem

del backend
