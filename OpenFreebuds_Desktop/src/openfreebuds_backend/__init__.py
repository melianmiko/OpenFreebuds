import platform

from openfreebuds_backend.dummy import *

if platform.system() == "Linux":
    from openfreebuds_backend.linux.ui_gtk import *
    from openfreebuds_backend.linux.bluez_io import *
    from openfreebuds_backend.linux.keybinder_io import *
    from openfreebuds_backend.linux.linux_misc import *
elif platform.system() == "Windows":
    from openfreebuds_backend.windows.bt_win32 import *
    from openfreebuds_backend.windows.ui_win32 import *
    from openfreebuds_backend.windows.misc_win32 import *
