"""响度增益控件的离屏测试：同步、置灰、不回滚、增益真的作用到样本上。"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

pytest.importorskip("PyQt6")
from PyQt6.QtWidgets import QApplication

from openfreebuds.driver.huawei.prompt_tone import TONE_AUTO_GAIN_TARGET
from openfreebuds_qt.app.dialog.tone_editor import OfbQtToneEditorDialog


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def dialog(app):
    samples = (np.sin(np.arange(8000) / 30.0) * 4000).astype("<i2")
    dlg = OfbQtToneEditorDialog(None, samples)
    yield dlg
    dlg.cleanup()


def test_auto_gain_is_default_and_disables_manual_controls(dialog):
    assert dialog.auto_gain is True
    assert dialog.gain_slider.isEnabled() is False
    assert dialog.gain_box.isEnabled() is False

    peak = int(np.max(np.abs(dialog.selection.astype(np.int32))))
    expected = 20 * np.log10(TONE_AUTO_GAIN_TARGET / peak)
    assert abs(dialog.gain_db - expected) < 0.02
    # 同一个值必须同时出现在滑块、数值框上，波形也按它重画
    assert abs(dialog.gain_box.value() - expected) < 0.02
    assert abs(dialog.gain_slider.value() - expected) < 0.01
    assert abs(dialog.waveform.gain_db - expected) < 0.01


def test_unchecking_keeps_best_value_instead_of_restoring(dialog):
    dialog.auto_gain_check.setChecked(False)
    dialog.gain_box.setValue(6.0)
    dialog.gain_slider.setValue(6.0, emit=True)
    assert dialog.gain_db == 6.0

    auto_value = dialog.gain_box.value() + 0  # 记录勾选前的值，仅用于对比
    dialog.auto_gain_check.setChecked(True)     # 勾选：回填最佳增益 + 置灰
    best = dialog.gain_db
    assert best != 6.0
    assert dialog.gain_box.isEnabled() is False
    # 勾选后展示值必须真的变了（之前的 bug 就是这里没刷新）
    assert abs(dialog.gain_box.value() - 6.0) > 0.1
    assert abs(dialog.gain_slider.value() - 6.0) > 0.1

    dialog.auto_gain_check.setChecked(False)    # 取消：保留最佳值，不回滚到 6.0
    assert dialog.gain_box.isEnabled() is True
    assert abs(dialog.gain_box.value() - best) < 0.01   # 数值框只显示两位小数
    assert dialog.gain_box.value() != 6.0
    assert auto_value == 6.0


def test_slider_and_box_stay_in_sync(dialog):
    dialog.auto_gain_check.setChecked(False)
    dialog.gain_slider.setValue(-12.0, emit=True)         # 用户拖滑块（浮点、无量化）
    assert dialog.gain_box.value() == -12.0
    dialog.gain_box.setValue(3.25)             # 用户在数值框里改（失焦/箭头）
    assert abs(dialog.gain_slider.value() - 3.25) < 1e-6
    assert dialog.gain_db == 3.25


def test_slider_is_continuous(dialog):
    """鼠标位置直接换算 dB，不再受 QSlider 整数步进限制。"""
    dialog.auto_gain_check.setChecked(False)
    dialog.resize(760, 460)
    track = dialog.gain_slider._track_rect()
    mid = track.left() + track.width() * 0.5
    dialog.gain_slider.setValue(dialog.gain_slider._db_at(mid + 0.5))
    assert dialog.gain_slider.value() == dialog.gain_slider._db_at(mid + 0.5)


def test_waveform_follows_gain(dialog):
    dialog.auto_gain_check.setChecked(False)
    dialog.gain_slider.setValue(12.0, emit=True)
    assert abs(dialog.waveform.gain_db - 12.0) < 1e-6
    # 波形按满响度基准（26213）画：抬高 12 dB 后包络显示值变大（可能顶到基准）
    peak = max(dialog.waveform._peaks)
    assert dialog.waveform._display_peak(peak) > peak
    assert dialog.waveform._display_peak(peak * 100) == 26213.0


def test_processed_samples_carry_the_gain(dialog):
    # 自动模式：峰值被抬到满响度基准（26213，APK 归一化峰值），且不越界
    auto = dialog.processed()
    assert abs(int(np.max(np.abs(auto.astype(np.int32)))) - TONE_AUTO_GAIN_TARGET) <= 1

    # 手动 0 dB：电平保持原样，证明增益不是被归一化抵消
    dialog.auto_gain_check.setChecked(False)
    dialog.gain_box.setValue(0.0)
    flat = dialog.processed()
    assert int(np.max(np.abs(flat.astype(np.int32)))) == int(
        np.max(np.abs(dialog.selection.astype(np.int32))))


def test_file_name_and_display_name_fields(app):
    """名字拆成「文件名（.pcm 为固定后缀）」和「显示名」两栏。"""
    samples = (np.sin(np.arange(4000) / 30.0) * 3000).astype("<i2")
    dlg = OfbQtToneEditorDialog(None, samples, "demo", "系统-演示样机")
    try:
        assert dlg.file_name == "demo"
        assert dlg.display_name == "系统-演示样机"
        # 后缀在框外，输入框里只有主体
        assert dlg.file_suffix_label.text() == ".pcm"
        assert ".pcm" not in dlg.file_edit.text()

        dlg.file_edit.setText("  new chime  ")
        dlg.display_edit.setText("  新的铃声  ")
        assert dlg.file_name == "new chime"
        assert dlg.display_name == "新的铃声"
    finally:
        dlg.cleanup()
