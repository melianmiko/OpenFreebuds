from PyQt6.QtWidgets import QSystemTrayIcon


class IOfbTrayIcon(QSystemTrayIcon):
    """
    Generic model for OpenFreebuds Tray Icon
    """

    async def boot(self):
        raise NotImplementedError("Not implemented")

    async def close(self):
        raise NotImplementedError("Not implemented")
