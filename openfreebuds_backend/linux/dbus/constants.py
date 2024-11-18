from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()

with open(SCRIPT_DIR / "xdg_desktop_portal.xml", "r") as f:
    XDG_DESKTOP_PORTAL_INTROSPECTION = f.read()
