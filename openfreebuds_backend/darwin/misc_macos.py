import logging
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

log = logging.getLogger("OfbDarwinBackend")

AUTOSTART_AVAILABLE = True
AUTOUPDATE_AVAILABLE = False  # Defer to Homebrew or DMG-based updates
GLOBAL_HOTKEYS_AVAILABLE = True  # pynput supports macOS (requires Accessibility permission)

_LAUNCH_AGENT_LABEL = "pw.mmk.OpenFreebuds"


def get_app_storage_path():
    return Path.home() / "Library" / "Application Support" / "openfreebuds"


def open_file(path):
    subprocess.Popen(["open", str(path)])


def is_run_at_boot():
    return _launch_agent_path().is_file()


async def set_run_at_boot(val):
    path = _launch_agent_path()
    if val:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            plistlib.dump(_build_launch_agent_plist(), f)
        log.debug(f"Wrote LaunchAgent: {path}")
        _launchctl("load", "-w", str(path))
    else:
        if path.is_file():
            _launchctl("unload", "-w", str(path))
            path.unlink()
            log.debug(f"Removed LaunchAgent: {path}")


def is_dark_taskbar():
    try:
        # NSUserDefaults reads the global preference set by macOS for the current user
        from Foundation import NSUserDefaults
        defaults = NSUserDefaults.standardUserDefaults()
        style = defaults.stringForKey_("AppleInterfaceStyle")
        return style == "Dark"
    except Exception:
        return None


# ---------------------------------------------------------------------------

def _launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{_LAUNCH_AGENT_LABEL}.plist"


def _program_arguments() -> list[str]:
    """Best-effort reconstruction of the command launchd should invoke."""
    cli = shutil.which("openfreebuds_qt")
    if cli:
        return [cli]
    # Fall back to the current Python with the entry-point module
    return [sys.executable, "-m", "openfreebuds_qt"]


def _build_launch_agent_plist() -> dict:
    return {
        "Label": _LAUNCH_AGENT_LABEL,
        "ProgramArguments": _program_arguments(),
        "RunAtLoad": True,
        "KeepAlive": False,
        "ProcessType": "Interactive",
    }


def _launchctl(*args: str) -> None:
    try:
        subprocess.run(
            ["launchctl", *args],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        log.debug("launchctl invocation failed", exc_info=True)
