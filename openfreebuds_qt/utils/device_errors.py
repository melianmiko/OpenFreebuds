from PyQt6.QtWidgets import QApplication

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
