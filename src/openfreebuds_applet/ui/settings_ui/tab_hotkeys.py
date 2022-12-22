import logging
import time
import tkinter
import webbrowser
from tkinter import ttk

from openfreebuds_applet.l18n import t
from openfreebuds_applet.modules import hotkeys, actions
from openfreebuds_applet.settings import SettingsStorage
from openfreebuds_applet.ui import tk_tools

log = logging.getLogger("SettingsHotkeysTab")


class HotkeysSettingsTab(ttk.Frame):
    def __init__(self, parent, applet):
        super().__init__(parent)
        self.applet = applet
        self.settings = applet.settings     # type: SettingsStorage
        self.is_recording = False
        self.av_error = ""
        self.recorder = hotkeys.HotkeyRecorder()
        self.grid()
        self.grid_columnconfigure(0, weight=1)

        self.var_main_sw = tkinter.BooleanVar(value=self.settings.enable_hotkeys)

        if not self._ui_available():
            return

        ttk.Checkbutton(self, text=t("prop_enabled"),
                        style="Switch.TCheckbutton",
                        variable=self.var_main_sw,
                        command=self._toggle_main)\
            .grid(row=0, sticky=tkinter.NW, padx=16, pady=16, columnspan=3)

        self.row_counter = 0
        self.hotkeys_root = ttk.Frame(self)
        self.hotkeys_root.grid_columnconfigure(0, weight=1)
        self._update_hotkeys_visible()

        all_actions = actions.get_action_names()
        for a in all_actions:
            self._add_hotkey(a, all_actions[a])

    def _update_hotkeys_visible(self):
        if self.var_main_sw.get():
            self.hotkeys_root.grid(column=0, row=3, sticky=tkinter.NSEW)
        else:
            self.hotkeys_root.grid_remove()

    def _add_hotkey(self, action, display_name):
        variable = tkinter.StringVar()

        st_val = "---"
        if action in self.settings.hotkeys_config_2:
            if self.settings.hotkeys_config_2[action] != "":
                st_val = self.settings.hotkeys_config_2[action]
        variable.set(st_val)

        def _on_click():
            if self.is_recording:
                return
            self._update_hotkey(variable, action)

        def _wipe():
            self.settings.hotkeys_config_2[action] = ""
            self.settings.write()
            hotkeys.start(self.applet)
            variable.set("---")

        ttk.Label(self.hotkeys_root, text=display_name) \
            .grid(row=self.row_counter, sticky="new", padx=16, pady=8, columnspan=3)
        ttk.Button(self.hotkeys_root, textvariable=variable, command=_on_click) \
            .grid(row=self.row_counter, column=1, sticky=tkinter.NSEW, pady=4)
        ttk.Button(self.hotkeys_root, text=t("clear"), command=_wipe) \
            .grid(row=self.row_counter, column=2, sticky=tkinter.NSEW, padx=4, pady=4)

        self.row_counter += 2

    def _update_hotkey(self, ui_var, action):
        self.is_recording = True
        self.recorder.record()
        ui_var.set("Press hotkey or ESC to cancel")

        start = time.time()

        def _check():
            log.debug("Waiting for hotkey")
            if not self.recorder.working:
                val = self.recorder.get_value()
                if val is not None:
                    log.debug("New hotkey action={} val={}".format(action, val))
                    self._apply_hotkey(action, val, ui_var)
                    return
            if time.time() - start > 10:
                log.debug("Hotkey record timed out, stopping...")
                self.recorder.cancel()
                ui_var.set('timeout')
                self.is_recording = False
                return
            self.after(250, _check)
        _check()

    def _apply_hotkey(self, action, val, ui_var):
        self.settings.hotkeys_config_2[action] = val
        self.settings.write()
        hotkeys.start(self.applet)

        ui_var.set(val)
        self.is_recording = False

    def _toggle_main(self):
        self.settings.enable_hotkeys = not self.settings.enable_hotkeys
        self.settings.write()
        self._update_hotkeys_visible()

        hotkeys.start(self.applet)

    def _show_compat_error_message(self):
        tk_tools.message(self.av_error, "OpenFreebuds")

    def _ui_available(self):
        is_available, av_error = hotkeys.test_available()
        if not is_available:
            log.warning(av_error)
            self.av_error = av_error
            ttk.Label(self, text=t("hotkeys_not_available")) \
                .grid(row=1, padx=16, pady=16, sticky=tkinter.NW)
            ttk.Button(self, text=t("show_error"),
                       command=self._show_compat_error_message) \
                .grid(row=2, padx=16, pady=4, sticky=tkinter.NW)
            return False

        is_supported, sp_error = hotkeys.test_os_supported()
        if not is_supported:
            log.warning(sp_error)
            ttk.Label(self, text=t("hotkeys_wayland")) \
                .grid(row=1, padx=16, pady=4, sticky=tkinter.NW, columnspan=4)
            link = ttk.Label(self, text=t("hotkeys_wayland_link"),
                             foreground="#04F", cursor="hand2")
            link.bind("<Button-1>", self.show_wayland_help)
            link.grid(row=2, padx=16, pady=8, sticky=tkinter.NW, columnspan=4)

        return True

    @staticmethod
    def show_wayland_help(_):
        webbrowser.open(t("hotkeys_wayland_url"))
