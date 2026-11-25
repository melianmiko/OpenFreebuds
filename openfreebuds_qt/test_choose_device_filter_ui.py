import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QCheckBox, QListWidget

from openfreebuds_qt.app.module.choose_device import DEVICE_NAME_ROLE, OfbQtChooseDeviceModule


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


class FakeModule:
    _render_list = OfbQtChooseDeviceModule._render_list

    def __init__(self):
        self.paired_list = QListWidget()
        self.show_unsupported_checkbox = QCheckBox()
        self._current_device_addr = ""
        self._device_rows = [
            {"name": "HUAWEI FreeClip 2", "address": "AA:BB:CC:DD:EE:01"},
            {"name": "HUAWEI FreeClip 2", "address": "AA:BB:CC:DD:EE:02"},
            {"name": "HUAWEI FreeBuds 5", "address": "AA:BB:CC:DD:EE:03"},
            {"name": "AirPods Pro", "address": "AA:BB:CC:DD:EE:04"},
            {"name": "Keyboard K380", "address": "AA:BB:CC:DD:EE:05"},
        ]


def labels(widget):
    return [widget.item(i).text() for i in range(widget.count())]


def raw_names(widget):
    return [widget.item(i).data(DEVICE_NAME_ROLE) for i in range(widget.count())]


def test_default_filter_and_duplicate_mac_labels(app):
    module = FakeModule()
    module._render_list()

    assert labels(module.paired_list) == [
        "HUAWEI FreeClip 2 [AA:BB:CC:DD:EE:01]",
        "HUAWEI FreeClip 2 [AA:BB:CC:DD:EE:02]",
        "HUAWEI FreeBuds 5",
    ]
    assert raw_names(module.paired_list) == [
        "HUAWEI FreeClip 2",
        "HUAWEI FreeClip 2",
        "HUAWEI FreeBuds 5",
    ]


def test_unsupported_toggle_restores_all_paired_devices(app):
    module = FakeModule()
    module.show_unsupported_checkbox.setChecked(True)
    module._render_list()

    assert labels(module.paired_list) == [
        "HUAWEI FreeClip 2 [AA:BB:CC:DD:EE:01]",
        "HUAWEI FreeClip 2 [AA:BB:CC:DD:EE:02]",
        "HUAWEI FreeBuds 5",
        "AirPods Pro",
        "Keyboard K380",
    ]
