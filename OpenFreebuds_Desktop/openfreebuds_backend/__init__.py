import platform

if platform.system() == "Linux":
    from openfreebuds_backend._linux import *
elif platform.system() == "Windows":
    from openfreebuds_backend._windows import *
else:
    raise Exception("OS not supported")
