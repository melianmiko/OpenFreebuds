from PIL import Image

from openfreebuds_qt.constants import ASSETS_PATH

ICON_SIZE = (64, 64)

# Images
ICON_LOADING = Image.open(ASSETS_PATH / "base_loading.png")
ICON_ANC_OFF = Image.open(ASSETS_PATH / "base_headset.png")
ICON_ANC_ON = Image.open(ASSETS_PATH / "base_headset_1.png")
ICON_ANC_AWR = Image.open(ASSETS_PATH / "base_headset_2.png")
ICON_OVERLAY_ERROR = Image.open(ASSETS_PATH / "overlay_error.png")
ICON_OVERLAY_SETUP = Image.open(ASSETS_PATH / "overlay_setup.png")

# Presets
PRESET_TRANSPARENT = Image.new("RGBA", ICON_SIZE, color="#00000000")
PRESET_LIGHT_MISSING = Image.new("RGBA", ICON_SIZE, color="#FFFFFF33")
PRESET_LIGHT_EMPTY = Image.new("RGBA", ICON_SIZE, color="#FFFFFF77")
PRESET_LIGHT_FULL = Image.new("RGBA", ICON_SIZE, color="#FFFFFFFF")
PRESET_DARK_MISSING = Image.new("RGBA", ICON_SIZE, color="#00000033")
PRESET_DARK_EMPTY = Image.new("RGBA", ICON_SIZE, color="#00000077")
PRESET_DARK_FULL = Image.new("RGBA", ICON_SIZE, color="#000000FF")
