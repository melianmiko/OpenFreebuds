import logging

from openfreebuds_applet.applet import FreebudsApplet

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s:%(name)s:%(threadName)s  %(message)s")


def main():
    applet = FreebudsApplet()
    applet.start()


main()

