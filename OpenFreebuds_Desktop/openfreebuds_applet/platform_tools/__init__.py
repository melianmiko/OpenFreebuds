import platform

if platform.system() == "Linux":
    from openfreebuds_applet.platform_tools._linux import *
elif platform.system() == "Windows":
    from openfreebuds_applet.platform_tools._windows import *
