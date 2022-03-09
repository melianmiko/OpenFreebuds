log_format = "%(levelname)s:%(name)s:%(threadName)s  %(message)s"

def start():
    from openfreebuds_applet.applet import FreebudsApplet
    FreebudsApplet().start()
