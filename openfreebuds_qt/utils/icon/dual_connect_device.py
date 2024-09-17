from PIL import Image
from PyQt6.QtWidgets import QApplication

from openfreebuds_qt.constants import ASSETS_PATH
from openfreebuds_qt.utils.draw import image_combine_mask

ICON_SIZE = (32, 32)

# Load files
BASE_DC_DEVICE_ICONS = {
    "device": Image.open(ASSETS_PATH / "dual_connect_device.png"),
}
OVERLAY_PLAYING = Image.open(ASSETS_PATH / "overlay_playing.png")
OVERLAY_PLAYING.thumbnail(ICON_SIZE)
OVERLAY_PRIMARY = Image.open(ASSETS_PATH / "overlay_primary.png")
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

        if is_connected:
            main_icon_color = palette.text().color().getRgb()
        else:
            main_icon_color = palette.placeholderText().color().getRgb()

        icon = image_combine_mask(BASE_DC_DEVICE_ICONS[kind],
                                  foreground=Image.new("RGBA", ICON_SIZE, color=main_icon_color),
                                  background=PRESET_TRANSPARENT)

        if is_playing:
            try:
                accent_color = palette.accent().color().getRgb()
            except AttributeError:
                accent_color = (0, 128, 256)
            overlay = image_combine_mask(OVERLAY_PLAYING,
                                         foreground=Image.new("RGBA", ICON_SIZE, color=accent_color),
                                         background=PRESET_TRANSPARENT)
            icon = Image.alpha_composite(icon, overlay)

        if is_primary:
            link_color = palette.link().color().getRgb()
            overlay = image_combine_mask(OVERLAY_PRIMARY,
                                         foreground=Image.new("RGBA", ICON_SIZE, color=link_color),
                                         background=PRESET_TRANSPARENT)
            icon = Image.alpha_composite(icon, overlay)

        _cached_icons[cache_key] = icon

    return _cached_icons[cache_key]


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    create_dual_connect_icon("device", True, True, True)
