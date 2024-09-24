import functools

from PIL import Image, ImageQt
from PyQt6.QtGui import QIcon

from openfreebuds_qt.constants import ASSETS_PATH
from openfreebuds_qt.utils.draw import image_combine_mask

ICON_SIZE = (64, 64)
PRESET_TRANSPARENT = Image.new("RGBA", ICON_SIZE, color="#00000000")


@functools.cache
def get_qt_icon_colored(name: str, color) -> QIcon:
    image = Image.open(ASSETS_PATH / f"icon/action/{name}.png")
    image = image_combine_mask(image,
                               foreground=Image.new("RGBA", ICON_SIZE, color=color),
                               background=PRESET_TRANSPARENT)

    return QIcon(ImageQt.toqpixmap(image))
