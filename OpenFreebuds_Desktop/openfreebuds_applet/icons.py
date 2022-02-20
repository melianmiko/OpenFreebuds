import logging

from PIL import Image, ImageDraw

from openfreebuds_applet import tools

ICON_SIZE = (32, 32)
ASSETS_PATH = tools.get_assets_path()


def spawn_color_image(size, color):
    return Image.new("RGBA", size, color=color)


class BaseImages:
    # Icons
    base = Image.open(ASSETS_PATH + "/base.png")
    mode_1 = Image.open(ASSETS_PATH + "/mode_1.png")
    mode_2 = Image.open(ASSETS_PATH + "/mode_2.png")

    # Color presets
    transparent = Image.new("RGBA", ICON_SIZE, color="#00000000")

    light_missing = Image.new("RGBA", ICON_SIZE, color="#FFFFFF33")
    light_empty = Image.new("RGBA", ICON_SIZE, color="#FFFFFF77")
    light_full = Image.new("RGBA", ICON_SIZE, color="#FFFFFFFF")

    dark_missing = Image.new("RGBA", ICON_SIZE, color="#00000033")
    dark_empty = Image.new("RGBA", ICON_SIZE, color="#00000077")
    dark_full = Image.new("RGBA", ICON_SIZE, color="#000000FF")

    theme_missing = light_missing
    theme_full = light_full
    theme_empty = light_empty


def set_theme(theme_name="auto"):
    value = theme_name
    if theme_name == "auto":
        from openfreebuds_applet.platform_tools import is_dark_theme
        value = "light" if is_dark_theme() else "dark"

    if value == "light":
        BaseImages.theme_missing = BaseImages.light_missing
        BaseImages.theme_full = BaseImages.light_full
        BaseImages.theme_empty = BaseImages.light_empty
    elif value == "dark":
        BaseImages.theme_missing = BaseImages.dark_missing
        BaseImages.theme_full = BaseImages.dark_full
        BaseImages.theme_empty = BaseImages.dark_empty
    else:
        raise Exception("Unknown theme value: " + value)

    logging.getLogger("AppletIcons").debug("set theme=" + value)


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


def get_icon_offline():
    return combine_mask(BaseImages.base,
                        foreground=BaseImages.theme_missing,
                        background=BaseImages.transparent)


def get_icon_device(battery, noise_mode):
    icon = BaseImages.base
    power_bg = combine_mask(spawn_power_bg_mask(battery / 100),
                            foreground=BaseImages.theme_full,
                            background=BaseImages.theme_empty)

    if noise_mode == 1:
        icon = BaseImages.mode_1
    elif noise_mode == 2:
        icon = BaseImages.mode_2

    return combine_mask(icon,
                        foreground=power_bg,
                        background=BaseImages.transparent)
