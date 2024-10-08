import functools

from PIL import Image, ImageQt
from PyQt6.QtGui import QPixmap

from openfreebuds_qt.constants import ASSETS_PATH
from openfreebuds_qt.utils.draw import image_combine_mask


@functools.cache
def get_img_colored(name: str, color, base_dir: str = "icon/action", scale_to = None) -> QPixmap:
    image = Image.open(ASSETS_PATH / f"{base_dir}/{name}.png")
    image = image_combine_mask(image,
                               foreground=Image.new("RGBA", image.size, color=color),
                               background=Image.new("RGBA", image.size, color="#00000000"))

    if scale_to:
        image.thumbnail(scale_to)

    return ImageQt.toqpixmap(image)
