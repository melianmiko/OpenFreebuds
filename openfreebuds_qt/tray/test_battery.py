import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("PyQt6")
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from openfreebuds import IOpenFreebuds
from openfreebuds_qt.tray.battery import battery_levels, battery_style
from openfreebuds_qt.tray.main import OfbTrayIcon


@pytest.mark.parametrize("data, expected", [
    ({"left": 0, "right": "100", "case": 85, "global": 0},
     {"left": 0, "right": 100, "case": 85}),
    ({"left": True, "right": -1, "case": 101}, {}),
    ({"global": "50"}, {}),
    ({"left": "--", "global": 50}, {}),
    (None, {}),
])
def test_reported_levels(data, expected):
    assert battery_levels(data) == expected


def test_invalid_saved_style_falls_back():
    config = SimpleNamespace(get=lambda *args: {"malformed": True})
    assert battery_style(config, "left") == ("#ffffff", "#202020", False, 100)


@pytest.mark.asyncio
async def test_tray_percentages_lifecycle(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    tray = QSystemTrayIcon()
    enabled = True
    tray.config = SimpleNamespace(
        get=lambda section, key, default=None: enabled if key == "tray_battery_percentages" else default,
        get_tray_icon_theme=lambda: "light"
    )
    tray.ofb = SimpleNamespace(
        get_property=AsyncMock(return_value={"left": 50, "right": 65, "case": 85}),
        get_device_tags=AsyncMock(return_value=("Test", "address")),
    )
    tray.menu = None
    tray._battery_icons = {}
    tray._battery_icon_values = {}
    tray._on_battery_click = lambda reason: None
    connected = IOpenFreebuds.STATE_CONNECTED
    try:
        await OfbTrayIcon._update_battery_icons(tray, connected)
        assert all(icon.isVisible() for icon in tray._battery_icons.values())
        assert "50%" in tray._battery_icons["left"].toolTip()
        tray.ofb.get_property.return_value = {"left": 100}
        await OfbTrayIcon._update_battery_icons(tray, connected)
        assert "100%" in tray._battery_icons["left"].toolTip()
        assert not tray._battery_icons["case"].isVisible()
        enabled = False
        await OfbTrayIcon._update_battery_icons(tray, connected)
        assert not any(icon.isVisible() for icon in tray._battery_icons.values())
        enabled = True
        await OfbTrayIcon._update_battery_icons(tray, connected)
        await OfbTrayIcon._update_battery_icons(tray, IOpenFreebuds.STATE_WAIT)
        assert not any(icon.isVisible() for icon in tray._battery_icons.values())
    finally:
        for icon in tray._battery_icons.values():
            icon.hide()
        tray.deleteLater()
        app.processEvents()


@pytest.mark.asyncio
async def test_appearance_settings_save_and_render(monkeypatch, tmp_path):
    from PyQt6.QtGui import QColor
    from openfreebuds_qt.tray.battery import percentage_icon
    from openfreebuds_qt.app.module.tray_battery import OfbQtTrayBatteryModule
    from openfreebuds_qt.config import OfbQtConfigParser
    import openfreebuds_qt.config.main as config_module

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(config_module, "CONFIG_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(OfbQtConfigParser, "instance", None)
    ofb = SimpleNamespace(send_message=AsyncMock())
    page = OfbQtTrayBatteryModule(None, SimpleNamespace(ofb=ofb))
    assert [page.component.itemData(i) for i in range(page.component.count())] == ["left", "right", "case"]
    await page.save("tray_battery_text_color", "#ff0000")
    await page.save("tray_battery_background_color", "#123456")
    assert OfbQtConfigParser().get("ui", "tray_battery_background_color") == "#123456"
    assert page.background_button.text() == "#123456"
    ofb.send_message.assert_awaited()
    image = percentage_icon(50, "light", "#ff0000", "#123456").pixmap(32, 32).toImage()
    assert image.pixelColor(0, 0) == QColor("#123456")
    assert any(image.pixelColor(x, y) == QColor("#ff0000") for x in range(32) for y in range(32))
    transparent = percentage_icon(100, "light", "#ff0000", None).pixmap(32, 32).toImage()
    assert transparent.pixelColor(0, 0).alpha() == 0
    from openfreebuds_qt.tray.battery import battery_style
    await page.save("tray_battery_left_text_color", "#00ff00")
    await page.save("tray_battery_left_font_scale", 60)
    await page.save("tray_battery_right_background_color", "#0000ff")
    assert battery_style(page.config, "left") == ("#00ff00", "#123456", False, 60)
    assert battery_style(page.config, "right") == ("#ff0000", "#0000ff", False, 100)
    page.component.setCurrentIndex(1)
    assert page.text_button.text() == "#ff0000"
    assert page.background_button.text() == "#0000ff"
    assert page.font_scale.value() == 100
    page.component.setCurrentIndex(0)
    assert page.font_scale.value() == 60
    reloaded = OfbQtConfigParser()
    assert battery_style(reloaded, "left")[3] == 60
    small = percentage_icon(50, "light", "#ff0000", None, 50).pixmap(32, 32).toImage()
    large = percentage_icon(50, "light", "#ff0000", None, 100).pixmap(32, 32).toImage()
    def painted_pixels(image):
        return sum(image.pixelColor(x, y).alpha() > 0 for x in range(32) for y in range(32))
    assert painted_pixels(small) < painted_pixels(large)
    page.deleteLater()
    app.processEvents()


@pytest.mark.asyncio
async def test_color_dialog_accept_and_cancel(monkeypatch, tmp_path):
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import QColorDialog
    from openfreebuds_qt.app.module.tray_battery import OfbQtTrayBatteryModule
    from openfreebuds_qt.config import OfbQtConfigParser
    import openfreebuds_qt.config.main as config_module

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(config_module, "CONFIG_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(OfbQtConfigParser, "instance", None)
    ofb = SimpleNamespace(send_message=AsyncMock())
    page = OfbQtTrayBatteryModule(None, SimpleNamespace(ofb=ofb))
    key = "tray_battery_left_text_color"
    task = asyncio.create_task(page.choose_color(key, "#ffffff"))
    await asyncio.sleep(0)
    dialog = next(dialog for dialog in page.findChildren(QColorDialog) if dialog.isVisible())
    dialog.setCurrentColor(QColor("#123456"))
    dialog.accept()
    await asyncio.wait_for(task, 2)
    assert page.config.get("ui", key) == "#123456"
    ofb.send_message.assert_awaited_once()

    task = asyncio.create_task(page.choose_color(key, "#ffffff"))
    await asyncio.sleep(0)
    dialog = next(dialog for dialog in page.findChildren(QColorDialog) if dialog.isVisible())
    dialog.setCurrentColor(QColor("#abcdef"))
    dialog.reject()
    await asyncio.wait_for(task, 2)
    assert page.config.get("ui", key) == "#123456"
    ofb.send_message.assert_awaited_once()
    page.deleteLater()
    app.processEvents()
