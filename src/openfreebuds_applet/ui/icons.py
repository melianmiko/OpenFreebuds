import logging

from PIL import Image, ImageDraw

from openfreebuds.manager import FreebudsManager
from openfreebuds_applet import utils

ICON_SIZE = (64, 64)
ASSETS_PATH = utils.get_assets_path()


def spawn_color_image(size, color):
    return Image.new("RGBA", size, color=color)


class BaseImages:
    # Icons
    loading = Image.open(ASSETS_PATH + "/base_loading.png")
    base = Image.open(ASSETS_PATH + "/base_headset.png")
    mode_cancellation = Image.open(ASSETS_PATH + "/base_headset_1.png")
    mode_awareness = Image.open(ASSETS_PATH + "/base_headset_2.png")
    overlay_error = Image.open(ASSETS_PATH + "/overlay_error.png")
    overlay_setup = Image.open(ASSETS_PATH + "/overlay_setup.png")

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
        import openfreebuds_backend
        value = "light" if openfreebuds_backend.is_dark_theme() else "dark"

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


def get_hash(state, battery=0, noise_mode=0):
    if state == FreebudsManager.STATE_WAIT or state == FreebudsManager.STATE_PAUSED:
        return "state_wait"
    elif state == FreebudsManager.STATE_OFFLINE:
        return "state_offline"
    elif state == FreebudsManager.STATE_FAILED or state == FreebudsManager.STATE_DISCONNECTED:
        return "state_fail"
    elif state == FreebudsManager.STATE_NO_DEV:
        return "state_no_dev"

    return "connected_{}_{}".format(noise_mode, battery)


def generate_icon(state, battery=0, noise_mode="normal"):
    if state == FreebudsManager.STATE_WAIT or state == FreebudsManager.STATE_PAUSED:
        icon = combine_mask(BaseImages.loading,
                            foreground=BaseImages.theme_full,
                            background=BaseImages.transparent)
        return icon
    elif state == FreebudsManager.STATE_OFFLINE:
        icon = combine_mask(BaseImages.base,
                            foreground=BaseImages.theme_missing,
                            background=BaseImages.transparent)
        return icon
    elif state == FreebudsManager.STATE_FAILED or state == FreebudsManager.STATE_DISCONNECTED:
        icon = combine_mask(BaseImages.base,
                            foreground=BaseImages.theme_missing,
                            background=BaseImages.transparent)
        icon.alpha_composite(BaseImages.overlay_error)
        return icon
    elif state == FreebudsManager.STATE_NO_DEV:
        icon = combine_mask(BaseImages.base,
                            foreground=BaseImages.theme_missing,
                            background=BaseImages.transparent)
        icon.alpha_composite(BaseImages.overlay_setup)
        return icon

    # Connected
    icon = BaseImages.base
    power_bg = combine_mask(spawn_power_bg_mask(battery / 100),
                            foreground=BaseImages.theme_full,
                            background=BaseImages.theme_empty)

    if noise_mode == "cancellation":
        icon = BaseImages.mode_cancellation
    elif noise_mode == "awareness":
        icon = BaseImages.mode_awareness

    result = combine_mask(icon,
                          foreground=power_bg,
                          background=BaseImages.transparent)

    return result
