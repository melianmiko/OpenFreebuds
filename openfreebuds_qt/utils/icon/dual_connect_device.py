from PIL import Image
from PyQt6.QtWidgets import QApplication

from openfreebuds_qt.constants import ASSETS_PATH
from openfreebuds_qt.utils.draw import image_combine_mask

ICON_SIZE = (32, 32)
DC_ICONS_PATH = ASSETS_PATH / "icon/dc"

# Load files
BASE_DC_DEVICE_ICONS = {
    "device": Image.open(DC_ICONS_PATH / "dual_connect_device.png"),
}
OVERLAY_PLAYING = Image.open(DC_ICONS_PATH / "overlay_playing.png")
OVERLAY_PLAYING.thumbnail(ICON_SIZE)
OVERLAY_PRIMARY = Image.open(DC_ICONS_PATH / "overlay_primary.png")
OVERLAY_PRIMARY.thumbnail(ICON_SIZE)

# Presets
PRESET_TRANSPARENT = Image.new("RGBA", ICON_SIZE, color="#00000000")

_cached_icons: dict[str, Image.Image] = {}


for key in BASE_DC_DEVICE_ICONS:
    BASE_DC_DEVICE_ICONS[key].thumbnail(ICON_SIZE)


def create_dual_connect_icon(
        kind: str = "device",
        is_primary: bool = False,
        is_playing: bool = False,
        is_connected: bool = False
) -> Image.Image:
    cache_key = f"{kind}_{is_connected}_{is_playing}_{is_primary}"

    if cache_key not in _cached_icons:
        palette = QApplication.palette()

        main_icon_color = palette.text().color().getRgb()
        if not is_connected:
            r, g, b, _ = main_icon_color
            main_icon_color = r, g, b, 128

        icon = image_combine_mask(BASE_DC_DEVICE_ICONS[kind],
                                  foreground=Image.new("RGBA", ICON_SIZE, color=main_icon_color),
                                  background=PRESET_TRANSPARENT)

        try:
            r, g, b, a = palette.accent().color().getRgb()
            accent_color = (255 - r, 255 - g, 255 - b, a)
        except AttributeError:
            accent_color = (255, 102, 0)

        if is_playing:
            overlay = image_combine_mask(OVERLAY_PLAYING,
                                         foreground=Image.new("RGBA", ICON_SIZE, color=accent_color),
                                         background=PRESET_TRANSPARENT)
            icon = Image.alpha_composite(icon, overlay)

        if is_primary:
            overlay = image_combine_mask(OVERLAY_PRIMARY,
                                         foreground=Image.new("RGBA", ICON_SIZE, color=accent_color),
                                         background=PRESET_TRANSPARENT)
            icon = Image.alpha_composite(icon, overlay)

        _cached_icons[cache_key] = icon

    return _cached_icons[cache_key]


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    create_dual_connect_icon("device", True, True, True)
