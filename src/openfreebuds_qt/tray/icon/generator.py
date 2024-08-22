from PIL import ImageDraw

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.tray.icon.base import *


def create_tray_icon(theme: str, state: int, battery: int, anc_mode: str) -> Image.Image:
    is_dark = theme == "dark"

    if state == IOpenFreebuds.STATE_WAIT or state == IOpenFreebuds.STATE_PAUSED:
        icon = _combine_mask(ICON_LOADING,
                             foreground=PRESET_DARK_FULL if is_dark else PRESET_LIGHT_FULL,
                             background=PRESET_TRANSPARENT)
        return icon
    elif state == IOpenFreebuds.STATE_DISCONNECTED:
        icon = _combine_mask(ICON_ANC_OFF,
                             foreground=PRESET_DARK_MISSING if is_dark else PRESET_LIGHT_MISSING,
                             background=PRESET_TRANSPARENT)
        return icon
    elif state == IOpenFreebuds.STATE_FAILED:
        icon = _combine_mask(ICON_ANC_OFF,
                             foreground=PRESET_DARK_MISSING if is_dark else PRESET_LIGHT_MISSING,
                             background=PRESET_TRANSPARENT)
        icon.alpha_composite(ICON_OVERLAY_ERROR)
        return icon
    elif state == IOpenFreebuds.STATE_STOPPED:
        icon = _combine_mask(ICON_ANC_OFF,
                             foreground=PRESET_DARK_MISSING if is_dark else PRESET_LIGHT_MISSING,
                             background=PRESET_TRANSPARENT)
        icon.alpha_composite(ICON_OVERLAY_SETUP)
        return icon

    # Connected
    power_bg = _combine_mask(_spawn_power_bg_mask(battery / 100),
                             foreground=PRESET_DARK_FULL if is_dark else PRESET_LIGHT_FULL,
                             background=PRESET_DARK_EMPTY if is_dark else PRESET_LIGHT_EMPTY)

    if anc_mode == "cancellation":
        icon = ICON_ANC_ON
    elif anc_mode == "awareness":
        icon = ICON_ANC_AWR
    else:
        icon = ICON_ANC_OFF

    result = _combine_mask(icon,
                           foreground=power_bg,
                           background=PRESET_TRANSPARENT)

    return result


def _spawn_power_bg_mask(level: float):
    img = Image.new("RGBA", ICON_SIZE, color="#ffffff")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, ICON_SIZE[0],
                    round(ICON_SIZE[1] * (1 - level))), fill="#000000")
    return img


def _combine_mask(mask: Image.Image, foreground: Image.Image, background: Image.Image) -> Image.Image:
    mask = mask.convert("RGBA")
    mask_data = mask.getdata()
    fg_data = foreground.getdata()

    img_data = list()
    for a, mask_pixel in enumerate(mask_data):
        img_data.append((fg_data[a][0], fg_data[a][1], fg_data[a][2],
                         round((fg_data[a][3] / 255) * mask_pixel[0])))

    generated = Image.new("RGBA", mask.size)

    # noinspection PyTypeChecker
    generated.putdata(img_data)

    out = Image.new("RGBA", mask.size)
    out.alpha_composite(background)
    out.alpha_composite(generated)

    return out


def _get_hash(state, battery=0, noise_mode=0):
    if state == IOpenFreebuds.STATE_WAIT or state == IOpenFreebuds.STATE_PAUSED:
        return "state_wait"
    elif state == IOpenFreebuds.STATE_DISCONNECTED:
        return "state_offline"
    elif state == IOpenFreebuds.STATE_FAILED:
        return "state_fail"
    elif state == IOpenFreebuds.STATE_STOPPED:
        return "state_no_dev"

    return "connected_{}_{}".format(noise_mode, battery)
