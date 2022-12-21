import re
from tkinter import Tk


def Get_HWND_DPI(window_handle):
    # To detect high DPI displays and avoid need to set Windows compatibility flags
    import os

    if os.name == "nt":
        from ctypes import windll, pointer, wintypes

        try:
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass  # this will fail on Windows Server and maybe early Windows
        DPI100pc = 96  # DPI 96 is 100% scaling
        DPI_type = 0  # MDT_EFFECTIVE_DPI = 0, MDT_ANGULAR_DPI = 1, MDT_RAW_DPI = 2
        winH = wintypes.HWND(window_handle)
        monitorhandle = windll.user32.MonitorFromWindow(
            winH, wintypes.DWORD(2)
        )  # MONITOR_DEFAULTTONEAREST = 2
        X = wintypes.UINT()
        Y = wintypes.UINT()
        try:
            windll.shcore.GetDpiForMonitor(
                monitorhandle, DPI_type, pointer(X), pointer(Y)
            )
            return X.value, Y.value, (X.value + Y.value) / (2 * DPI100pc)
        except Exception:
            return 96, 96, 1  # Assume standard Windows DPI & scaling
    else:
        return None, None, 1  # What to do for other OSs?


def TkGeometryScale(s, cvtfunc):
    patt = r"(?P<W>\d+)x(?P<H>\d+)\+(?P<X>\d+)\+(?P<Y>\d+)"  # format "WxH+X+Y"
    R = re.compile(patt).search(s)
    G = str(cvtfunc(R.group("W"))) + "x"
    G += str(cvtfunc(R.group("H"))) + "+"
    G += str(cvtfunc(R.group("X"))) + "+"
    G += str(cvtfunc(R.group("Y")))
    return G


def MakeTkDPIAware(TKGUI):
    TKGUI.DPI_X, TKGUI.DPI_Y, TKGUI.DPI_scaling = Get_HWND_DPI(TKGUI.winfo_id())
    TKGUI.TkScale = lambda v: int(float(v) * TKGUI.DPI_scaling)
    TKGUI.TkGeometryScale = lambda s: TkGeometryScale(s, TKGUI.TkScale)


def HdpiTk():
    root = Tk()
    MakeTkDPIAware(root)
    return root
