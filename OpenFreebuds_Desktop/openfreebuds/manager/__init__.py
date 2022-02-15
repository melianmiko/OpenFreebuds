import platform


def create():
    if platform.system() == "Linux":
        from openfreebuds.manager.linux import LinuxFreebudsManager
        return LinuxFreebudsManager()
    elif platform.system() == "Windows":
        from openfreebuds.manager.windows import WindowsFreebudsManager
        return WindowsFreebudsManager()

    raise Exception("Platform not supported")
