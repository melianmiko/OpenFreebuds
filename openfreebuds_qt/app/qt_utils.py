import asyncio
import os
import traceback
from contextlib import contextmanager, asynccontextmanager, suppress

from PyQt6.QtWidgets import QComboBox, QWidget, QMessageBox, QBoxLayout

from openfreebuds.utils.logger import create_logger
from openfreebuds_qt.addons.report_tool import OfbQtReportTool
from openfreebuds_qt.app.dialog.error_dialog import OfbQtErrorDialog
from openfreebuds_qt.generic import IOfbQtContext

log = create_logger("OfbQtUtils")


def widget_with_layout(parent: QWidget, direction: QBoxLayout.Direction):
    root = QWidget(parent)
    root_layout = QBoxLayout(direction)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)
    root.setLayout(root_layout)
    parent.layout().addWidget(root)
    return root, root_layout


@asynccontextmanager
async def qt_error_handler(identifier, ctx: IOfbQtContext):
    # noinspection PyBroadException
    try:
        if getattr(ctx, "exit", None) is None:
            raise Exception(f"QtErrorHandler for {identifier} missing root context link")
        yield
    except Exception:
        log.exception(f"Got exception for {identifier}")

        exception = traceback.format_exc()
        await OfbQtErrorDialog(ctx).get_user_response(exception)

        with suppress(Exception):
            async with asyncio.Timeout(5):
                await OfbQtReportTool(ctx).create_and_show()
                await ctx.exit(1)

        # Kill process
        # noinspection PyProtectedMember,PyUnresolvedReferences
        os._exit(1)


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


# noinspection PyUnresolvedReferences
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
