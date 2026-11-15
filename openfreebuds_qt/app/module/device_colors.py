from PyQt6.QtCore import QCoreApplication

# Chinese color names from the official cloud config, mapped to an English
# source string which is then translated by Qt using the "DeviceColor" context.
COLOR_NAME_EN = {
    "白色": "White",
    "黑色": "Black",
    "蓝色": "Blue",
    "紫色": "Purple",
    "玫瑰金": "Rose gold",
    "红色": "Red",
    "黄色": "Yellow",
    "星河蓝": "Starry blue",
    "红黄混色": "Red-yellow",
    "红蓝混色": "Red-blue",
    "蓝黄混色": "Blue-yellow",
    "黄红混色": "Yellow-red",
    "蓝红混色": "Blue-red",
    "黄蓝混色": "Yellow-blue",
    "绿色": "Green",
    "灰色": "Grey",
    "粉色": "Pink",
    "橙色": "Orange",
    "金色": "Gold",
    "银色": "Silver",
    "米色": "Beige",
    "卡其色": "Khaki",
    "浅紫色": "Light purple",
    "蓝紫色": "Blue-purple",
    "米白": "Off-white",
    "银白色": "Silver white",
    "陶瓷白": "Ceramic white",
    "冰霜银": "Frost silver",
    "曜石黑": "Obsidian black",
    "樱语粉": "Cherry pink",
    "天空蓝": "Sky blue",
    "薄荷绿": "Mint green",
    "鎏金黑": "Gilded black",
    "流光紫": "Gradient purple",
    "海岛蓝": "Island blue",
    "晨曦金": "Dawn gold",
    "冰晶蓝": "Ice blue",
    "云杉绿": "Spruce green",
    "典雅黑": "Elegant black",
    "陶瓷黑": "Ceramic black",
    "流光金": "Gradient gold",
}


def translate_color_name(name: str) -> str:
    """
    Translate an official color name for the current UI language.
    """
    source = COLOR_NAME_EN.get(name)
    if not source:
        return name
    return QCoreApplication.translate("DeviceColor", source)
