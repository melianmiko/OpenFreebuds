log_format = "%(levelname)s:%(name)s:%(threadName)s  %(message)s"


def create():
    from openfreebuds_applet.applet import FreebudsApplet
    return FreebudsApplet()
