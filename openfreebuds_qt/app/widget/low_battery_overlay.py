from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from openfreebuds_qt.utils import get_img_colored


class LowBatteryOverlay(QWidget):
    DISPLAY_MS = 3000
    SHOW_DURATION_MS = 230
    HIDE_DURATION_MS = 180
    SLIDE_OFFSET = 22
    TOP_MARGIN = 18
    ICON_COLOR = (244, 246, 248, 255)
    VALUE_COLOR_DEFAULT = "#f4f6f8"
    VALUE_COLOR_WARNING = "#ffb454"
    VALUE_COLOR_CRITICAL = "#ff5f57"
    WIDTH_BY_ITEM_COUNT = {
        1: 148,
        2: 182,
        3: 214,
    }

    def __init__(self, device_name: str, battery: dict, threshold: int):
        super().__init__(None)

        del threshold
        self._show_animation = None
        self._hide_animation = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide_overlay)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        frame = QFrame(self)
        frame.setObjectName("lowBatteryOverlayFrame")
        frame.setStyleSheet("""
            #lowBatteryOverlayFrame {
                background-color: #17191d;
                border: 1px solid rgba(255, 255, 255, 38);
                border-radius: 14px;
            }
            QLabel {
                color: #f4f6f8;
                background: transparent;
            }
            QLabel[role="title"] {
                font-size: 12px;
                font-weight: 600;
            }
            QLabel[role="value"] {
                font-size: 13px;
                font-weight: 600;
            }
        """)
        root.addWidget(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(7)

        title = QLabel(device_name or "OpenFreebuds", frame)
        title.setProperty("role", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setMaximumHeight(18)
        layout.addWidget(title)

        battery_layout = QHBoxLayout()
        battery_layout.setSpacing(12)
        battery_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(battery_layout)

        battery_items = self._battery_items(battery)
        for key, value in battery_items:
            item = QHBoxLayout()
            item.setSpacing(4)
            item.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon = QLabel(frame)
            icon.setFixedSize(18, 18)
            icon_pixmap = self._battery_icon(key)
            if icon_pixmap is not None:
                icon.setPixmap(icon_pixmap)
            item.addWidget(icon)

            value_label = QLabel(f"{value}%", frame)
            value_label.setProperty("role", "value")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_label.setStyleSheet(f"color: {self._battery_value_color(key, value)};")
            item.addWidget(value_label)

            battery_layout.addLayout(item)

        self.setFixedWidth(self.WIDTH_BY_ITEM_COUNT.get(len(battery_items), 214))
        self.adjustSize()

    def show_overlay(self):
        screen = QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry()
        x = geometry.x() + (geometry.width() - self.width()) // 2
        visible_y = geometry.y() + self.TOP_MARGIN
        hidden_y = visible_y - self.height() - self.SLIDE_OFFSET

        self.move(x, hidden_y)
        self.show()
        self.raise_()

        self._show_animation = QPropertyAnimation(self, b"pos", self)
        self._show_animation.setDuration(self.SHOW_DURATION_MS)
        self._show_animation.setStartValue(QPoint(x, hidden_y))
        self._show_animation.setEndValue(QPoint(x, visible_y))
        self._show_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._show_animation.finished.connect(lambda: self._hide_timer.start(self.DISPLAY_MS))
        self._show_animation.start()

    def hide_overlay(self):
        if not self.isVisible():
            return

        self._hide_timer.stop()
        end_pos = QPoint(self.x(), self.y() - self.height() - self.SLIDE_OFFSET)
        self._hide_animation = QPropertyAnimation(self, b"pos", self)
        self._hide_animation.setDuration(self.HIDE_DURATION_MS)
        self._hide_animation.setStartValue(self.pos())
        self._hide_animation.setEndValue(end_pos)
        self._hide_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self._hide_animation.finished.connect(self.close)
        self._hide_animation.start()

    def closeEvent(self, event):
        self._hide_timer.stop()
        if self._show_animation is not None:
            self._show_animation.stop()
        if self._hide_animation is not None:
            self._hide_animation.stop()
        event.accept()

    def _battery_items(self, battery: dict):
        if all(key in battery for key in ("left", "right", "case")):
            return [
                ("left", battery["left"]),
                ("right", battery["right"]),
                ("case", battery["case"]),
            ]

        rows = []
        for key in ("left", "right", "case", "global"):
            if key in battery:
                rows.append((key, battery[key]))

        return rows or [("global", "--")]

    @classmethod
    def _battery_icon(cls, key: str):
        icon_name = {
            "left": "batt_l",
            "right": "batt_r",
            "case": "batt_c",
            "global": "batt_c",
        }.get(key, "batt_c")

        try:
            return get_img_colored(icon_name, cls.ICON_COLOR, "icon/main_window", (18, 18))
        except Exception:
            return None

    @classmethod
    def _battery_value_color(cls, key: str, value):
        if key not in ("left", "right") or isinstance(value, bool) or not isinstance(value, int):
            return cls.VALUE_COLOR_DEFAULT
        if value <= 10:
            return cls.VALUE_COLOR_CRITICAL
        if value <= 20:
            return cls.VALUE_COLOR_WARNING
        return cls.VALUE_COLOR_DEFAULT
