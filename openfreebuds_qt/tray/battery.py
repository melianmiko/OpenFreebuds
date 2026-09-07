from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPixmap


def battery_levels(battery):
    """Return only reported, valid levels; never invent a zero for missing data."""
    if not isinstance(battery, dict):
        return {}
    keys = ("left", "right", "case")
    levels = {}
    for key in keys:
        value = battery.get(key)
        if isinstance(value, str) and value.isascii() and value.isdigit():
            value = int(value)
        if type(value) is int and 0 <= value <= 100:
            levels[key] = value
    return levels


def battery_style(config, key):
    """Per-component overrides inherit existing shared settings."""
    def value(name, default):
        shared = config.get("ui", f"tray_battery_{name}", default)
        return config.get("ui", f"tray_battery_{key}_{name}", shared)
    text = value("text_color", "#ffffff")
    background = value("background_color", "#202020")
    if not isinstance(text, str) or not QColor(text).isValid():
        text = "#ffffff"
    if not isinstance(background, str) or not QColor(background).isValid():
        background = "#202020"
    transparent = value("transparent", False)
    transparent = transparent if isinstance(transparent, bool) else False
    scale = value("font_scale", 100)
    scale = max(50, min(100, scale)) if type(scale) is int else 100
    bold = value("bold", True)
    bold = bold if isinstance(bold, bool) else True
    return text, background, transparent, scale, bold


def percentage_icon(level: int, theme: str, text_color=None, background_color=None, font_scale=100, bold=True) -> QIcon:
    """Render numeric battery levels at native tray sizes for each DPI."""
    icon = QIcon()
    for size in (16, 20, 24, 32, 48, 64):
        pixmap = QPixmap(size, size)
        background = QColor(background_color) if isinstance(background_color, str) else QColor()
        pixmap.fill(background if background.isValid() else Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        foreground = QColor(text_color) if isinstance(text_color, str) else QColor()
        painter.setPen(foreground if foreground.isValid() else QColor(
            "#161616" if theme == "dark" else "#ffffff"
        ))
        font = QFont("Segoe UI")
        font.setBold(bold)
        text = str(level)
        for pixels in range(size, 3, -1):
            font.setPixelSize(pixels)
            metrics = QFontMetrics(font)
            if metrics.horizontalAdvance(text) <= size and metrics.height() <= size:
                break
        font.setPixelSize(max(4, round(font.pixelSize() * font_scale / 100)))
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        icon.addPixmap(pixmap)
    return icon
