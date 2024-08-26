import asyncio
from contextlib import contextmanager

from PyQt6.QtWidgets import QComboBox, QWidget, QDialog, QMessageBox


def fill_combo_box(box: QComboBox, options: list[str], name_map: dict[str, str], current: str):
    box.blockSignals(True)
    box.clear()
    box.addItems([box.tr(name_map.get(i, i)) for i in options])
    for index, value in enumerate(options):
        box.setItemData(index, value)

    if current in options:
        box.setCurrentIndex(options.index(current))
    else:
        box.setCurrentIndex(-1)

    box.blockSignals(False)


async def exec_msg_box_async(dialog: QMessageBox):
    event = asyncio.Event()

    def on_exit():
        event.set()

    dialog.buttonClicked.connect(on_exit)
    dialog.finished.connect(on_exit)
    dialog.show()
    await event.wait()
    dialog.hide()

    return dialog.result()


@contextmanager
def blocked_signals(widget: QWidget):
    try:
        widget.blockSignals(True)
        yield widget
    finally:
        widget.blockSignals(False)
