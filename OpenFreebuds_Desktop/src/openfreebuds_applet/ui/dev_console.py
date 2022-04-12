import tkinter
from tkinter import ttk

from openfreebuds import cli_io
from openfreebuds.manager import FreebudsManager
from openfreebuds_applet.ui import tk_tools

HELP = """
Use this only if you know what you're doing.

 * `l` - list all device properties
 * `set [group] [name] [int_value]` - set integer property value
 * `set_str [group] [name] [value]` - set string property value
 * `w [ints...]` - build a package and send them to device (danger)

"""


@tk_tools.ui_thread
def start(manager: FreebudsManager):
    window = tkinter.Toplevel()
    window.wm_title("OpenFreebuds Dev console")
    window.wm_geometry("800x600")
    window.grid_columnconfigure(0, weight=1)

    var_input = tkinter.StringVar()
    font = tkinter.font.Font(family="monospace", size=10)

    output_widget = ttk.Label(window, text=HELP, font=font)
    input_widget = ttk.Entry(window, textvariable=var_input)

    def do_command(_):
        command = var_input.get().split(" ")
        if manager.state == manager.STATE_CONNECTED:
            result = cli_io.dev_command(manager.device, command)
        else:
            result = "Device don't connected"
        output_widget.configure(text=result)
        var_input.set("")

    input_widget.grid(sticky=tkinter.NSEW)
    output_widget.grid(sticky=tkinter.NSEW, row=1, padx=10, pady=10)

    window.bind('<Return>', do_command)
