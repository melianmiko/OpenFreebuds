import asyncio

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QWidget


class OfbQtAsyncDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._result = False
        self._event = asyncio.Event()
        self.setWindowModality(Qt.WindowModality.WindowModal)

    async def get_user_response(self):
        self._event = asyncio.Event()
        self.show()
        await self._event.wait()
        self.hide()
        return self._result

    def accept(self):
        self._result = True
        self._event.set()

    def reject(self):
        self._result = False
        self._event.set()