import asyncio

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QWidget


# noinspection PyUnresolvedReferences
async def run_dialog_async(dialog: QDialog):
    result = asyncio.Queue()

    def accept():
        result.put_nowait(True)

    def reject():
        result.put_nowait(False)

    dialog.accepted.connect(accept)
    dialog.rejected.connect(reject)
    dialog.show()
    out = await result.get()
    dialog.hide()

    return out


class OfbQtAsyncDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.WindowModal)

    async def get_user_response(self):
        return await run_dialog_async(self)
