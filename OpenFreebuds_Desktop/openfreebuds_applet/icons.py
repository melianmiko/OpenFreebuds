import PIL.Image
from PIL import Image, ImageDraw

ICON_SIZE = (24, 24)


def spawn_color_image(size, color):
    return Image.new("RGBA", size, color=color)


class BaseImages:
    transparent = Image.new("RGBA", ICON_SIZE, color="#00000000")
    light_missing = Image.new("RGBA", ICON_SIZE, color="#FFFFFF22")
    light_empty = Image.new("RGBA", ICON_SIZE, color="#FFFFFF44")
    light_full = Image.new("RGBA", ICON_SIZE, color="#FFFFFFFF")

    theme_missing = light_missing
    theme_full = light_full
    theme_empty = light_empty


def spawn_power_bg_mask(level: float):
    img = Image.new("RGBA", ICON_SIZE, color="#ffffff")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, ICON_SIZE[0],
                    round(ICON_SIZE[1] * (1 - level))), fill="#000000")
    return img


# noinspection PyTypeChecker
def combine_mask(mask, foreground=None, background=None):
    mask = mask.convert("RGBA")
    mask_data = mask.getdata()
    fg_data = foreground.getdata()

    img_data = list()
    for a, mask_pixel in enumerate(mask_data):
        img_data.append((fg_data[a][0], fg_data[a][1], fg_data[a][2],
                         round((fg_data[a][3] / 255) * mask_pixel[0])))

    generated = Image.new("RGBA", mask.size)
    generated.putdata(img_data)

    out = Image.new("RGBA", mask.size)
    out.alpha_composite(background)
    out.alpha_composite(generated)

    return out


def _get_base_device():
    # Generate an image and draw a pattern
    image = Image.new('RGBA', ICON_SIZE, "#000000")
    dc = ImageDraw.Draw(image)
    dc.rectangle((0, 0, ICON_SIZE[0], ICON_SIZE[1]), fill="#FFFFFF")

    return image


def get_icon_offline():
    return combine_mask(_get_base_device(),
                        foreground=BaseImages.theme_missing,
                        background=BaseImages.transparent)


def get_icon_device(battery, noise_mode):
    icon = _get_base_device()

    power_bg = combine_mask(spawn_power_bg_mask(battery / 100),
                            foreground=BaseImages.theme_full,
                            background=BaseImages.theme_empty)
    return combine_mask(icon,
                        foreground=power_bg,
                        background=BaseImages.transparent)
