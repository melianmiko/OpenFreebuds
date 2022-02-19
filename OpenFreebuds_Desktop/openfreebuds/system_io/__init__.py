import platform

if platform.system() == "Linux":
    from openfreebuds.system_io._linux import *
elif platform.system() == "Windows":
    from openfreebuds.system_io._windows import *
else:
    raise Exception("OS not supported")
