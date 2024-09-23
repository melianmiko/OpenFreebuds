from argparse import ArgumentParser

from openfreebuds_qt.main import OfbQtApplication
from openfreebuds_qt.version_info import VERSION

parser = ArgumentParser(
    prog="openfreebuds_qt",
    description="Client application for HUAWEI Bluetooth headphones",
    epilog=f"by melianmiko | mmk.pw | {VERSION}"
)
parser.add_argument("-v", "--verbose",
                    action="store_true",
                    help="Verbose log output")
parser.add_argument("-l", "--dont-ignore-logs",
                    action="store_true",
                    help="Don't exclude third-party libraries logs")
parser.add_argument('-c', '--client',
                    action="store_true",
                    help="Client-mode, allows to start multiple app instances from the same user")
parser.add_argument('-s', '--settings',
                    action="store_true",
                    help="Open settings after launch")
parser.add_argument('--virtual-device',
                    help="Use virtual debug device, for UI testing")
parser.add_argument("shortcut",
                    nargs="?", default="",
                    help="Execute shortcut operation in using OpenFreebuds")


def main():
    args = parser.parse_args()
    OfbQtApplication.start(args)


if __name__ == "__main__":
    main()
