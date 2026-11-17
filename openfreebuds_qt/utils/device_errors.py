from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget

# Mirrors SPP_PORT_BUSY from openfreebuds.driver.generic.spp; kept here as a plain
# string so the RPC boundary needs no extra imports.
SPP_PORT_BUSY = "spp_port_busy"


def startup_error_code(error: Exception) -> str:
    """Return the first string argument of a driver error, unwrapping RPC wrappers."""
    args = getattr(error, "args", ())
    if args and isinstance(args[0], str):
        return args[0]
    return ""


def spp_port_busy_message() -> str:
    return QApplication.translate(
        "OfbQtDeviceErrors",
        "Connection failed. Check whether another app is occupying the Bluetooth port "
        "(such as Huawei PC Manager, Huawei Control Center or MagicPods).",
    )


async def show_spp_port_busy_dialog(parent: QWidget):
    """Small standalone notice; the generic error dialog implies a crash and a bug report."""
    # Imported here to keep this module free of heavy Qt dialog dependencies at startup
    from openfreebuds_qt.utils.qt_utils import exec_msg_box_async

    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(QApplication.translate("OfbQtDeviceErrors", "Connection failed"))
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setText(spp_port_busy_message())
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.button(QMessageBox.StandardButton.Ok).setText(
        QApplication.translate("OfbQtDeviceErrors", "Close")
    )
    await exec_msg_box_async(box)
