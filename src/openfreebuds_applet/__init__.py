log_format = "%(levelname)s:%(name)s:%(threadName)s  %(message)s"
base_logger_names = [
    "SPPDevice", "FreebudsManager", "BaseDevice",
    "Applet", "LinuxBackend", "WindowsBackend"
]

def create():
    from openfreebuds_applet.applet import FreebudsApplet
    return FreebudsApplet()
