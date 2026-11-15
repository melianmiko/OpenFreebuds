"""自定义提示音编辑器：波形 + 双指针裁剪 + 播放/暂停 + 响度增益 + 中英文命名。

裁剪上限 6 秒（设备 PCM 上限），输出 Signed 16bit / 16755Hz / Mono PCM。
响度增益：手动滑块（-36…+36 dB，0.1 dB 一档）或勾选「自动增益响度」自动抬到不爆电平。
"""
import os
import tempfile
import wave
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QRect, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from openfreebuds.driver.huawei.prompt_tone import (
    TONE_MAX_DURATION,
    TONE_MAX_SAMPLES,
    TONE_SAMPLE_RATE,
    apply_gain_db,
    peak_gain_db,
)

MIN_SECONDS = 0.2
GAIN_MIN_DB = -36.0
GAIN_MAX_DB = 36.0
TONE_FULL_SCALE = 26213.0   # 满响度基准 = APK 的归一化峰值(0.8*32767)，波形上下限也按它画


class ToneWaveform(QWidget):
    """波形图 + 起止双指针，拖动即调整裁剪范围；增益变化时按新电平重绘。"""

    range_changed = pyqtSignal(int, int)
    HANDLE_GRAB_PX = 12
    ENVELOPE_BINS = 512

    def __init__(self, samples: np.ndarray, parent: QWidget | None = None):
        super().__init__(parent)
        self.samples = samples
        self.total = max(1, samples.size)
        # 包络在这里就算好并转成纯 Python 列表：paintEvent 里不碰 numpy，避免绘制期间出问题
        self._peaks = self._compute_peaks(samples).tolist()
        self._gain_db = 0.0
        self.start = 0
        self.end = min(self.total, TONE_MAX_SAMPLES)
        self._drag = ""
        self.setMinimumHeight(110)
        self.setMouseTracking(True)

    # --- 状态 ---------------------------------------------------------
    def set_gain(self, gain_db: float):
        """响度增益一变，波形就按新电平重画（超过满刻度的部分会被削平）。"""
        gain_db = float(gain_db)
        if gain_db != self._gain_db:
            self._gain_db = gain_db
            self.update()

    @property
    def gain_db(self) -> float:
        return self._gain_db

    def _display_peak(self, peak: float) -> float:
        """包络乘以增益，按满刻度截断——这就是最终进 PCM 的电平。"""
        return min(TONE_FULL_SCALE, peak * (10.0 ** (self._gain_db / 20.0)))


    @classmethod
    def _compute_peaks(cls, samples: np.ndarray) -> np.ndarray:
        """预先算好包络（512 个桶），paintEvent 里只做查表，避免在绘制中跑 numpy 分片。"""
        bins = cls.ENVELOPE_BINS
        if samples.size == 0:
            return np.zeros(bins, dtype=np.float64)
        chunk = max(1, samples.size // bins)
        usable = samples[:chunk * bins].astype(np.int32)
        return np.abs(usable.reshape(bins, chunk)).max(axis=1).astype(np.float64)

    # --- 状态 ---------------------------------------------------------
    def set_range(self, start: int, end: int):
        min_len = int(MIN_SECONDS * TONE_SAMPLE_RATE)
        max_len = TONE_MAX_SAMPLES
        start = max(0, min(start, self.total - min_len))
        end = max(start + min_len, min(end, self.total, start + max_len))
        if (start, end) != (self.start, self.end):
            self.start, self.end = start, end
            self.update()
            self.range_changed.emit(start, end)

    def _x_of(self, index: int) -> float:
        return self.rect().left() + index / self.total * self.rect().width()

    def _index_of(self, x: float) -> int:
        width = max(1, self.rect().width())
        return int(max(0, min(self.total, (x - self.rect().left()) / width * self.total)))

    # --- 事件 ---------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x = event.position().x()
        if abs(x - self._x_of(self.start)) <= self.HANDLE_GRAB_PX:
            self._drag = "start"
        elif abs(x - self._x_of(self.end)) <= self.HANDLE_GRAB_PX:
            self._drag = "end"
        elif self._x_of(self.start) < x < self._x_of(self.end):
            self._drag = "mid"
            self._drag_offset = self._index_of(x) - self.start
        else:
            index = self._index_of(x)
            span = self.end - self.start
            if index < self.start:
                self.set_range(index, index + span)
            else:
                self.set_range(index - span, index)
            return
        self.mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        x = event.position().x()
        if self._drag == "start":
            self.set_range(self._index_of(x), self.end)
        elif self._drag == "end":
            self.set_range(self.start, self._index_of(x))
        elif self._drag == "mid":
            span = self.end - self.start
            start = self._index_of(x) - getattr(self, "_drag_offset", span // 2)
            self.set_range(start, start + span)

    def mouseReleaseEvent(self, event):
        self._drag = ""
        self.setCursor(Qt.CursorShape.ArrowCursor)

    # --- 绘制 ---------------------------------------------------------
    def paintEvent(self, event):
        try:
            self._paint(event)
        except Exception:  # 绘制异常绝不能冒到 Qt 虚拟函数里，否则 PyQt6 会直接 abort 掉进程
            import traceback
            traceback.print_exc()

    def _paint(self, event):
        painter = QPainter(self)
        rect = QRect(self.rect())   # 不再留上下边距：波形直接铺满整个控件
        painter.fillRect(self.rect(), QColor("#202028"))

        width = max(1, rect.width())
        peaks = self._peaks
        bins = len(peaks)
        top = rect.top() + rect.height() / 2
        # 按满响度基准（26213）作参考：增益一调，波形就变高/被削平，能直观看出会不会超过满响度
        scale = (rect.height() / 2) / TONE_FULL_SCALE

        pen_bar = QPen(QColor("#7f86b0"), 1)
        painter.setPen(pen_bar)
        for x in range(width):
            peak = peaks[min(bins - 1, x * bins // width)] if bins else 0.0
            shown = self._display_peak(peak)
            height = min(rect.height() / 2, shown * scale)
            x_pos = rect.left() + x
            painter.drawLine(x_pos, int(top - height), x_pos, int(top + height))

        sel_left = int(self._x_of(self.start))
        sel_right = int(self._x_of(self.end))
        painter.fillRect(QRect(sel_left, rect.top(), max(1, sel_right - sel_left), rect.height()),
                         QColor(255, 204, 102, 40))

        pen_handle = QPen(QColor("#ffcc66"), 2)
        painter.setPen(pen_handle)
        for index in (self.start, self.end):
            x = int(self._x_of(index))
            painter.drawLine(x, rect.top(), x, rect.bottom())
            painter.drawRect(x - 3, int(top) - 4, 6, 8)


class GainSlider(QWidget):
    """0 刻度居中的连续增益滑块。

    QSlider 只能存整数、还要按像素取整，拖起来是「一格一格」的；这里直接用浮点
    按鼠标位置换算 dB，做到真正的无级拖动，刻度只保留中间的 0 dB。
    """

    value_changed = pyqtSignal(float)   # 拖动过程中持续发出（用于同步数值框/波形）
    released = pyqtSignal()             # 松手时发出一次（用于「立即生效」）
    HANDLE_RADIUS = 6
    SIDE_MARGIN = 10

    def __init__(self, min_db: float = GAIN_MIN_DB, max_db: float = GAIN_MAX_DB,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._min = float(min_db)
        self._max = float(max_db)
        self._value = 0.0
        self._dragging = False
        self.setMinimumHeight(26)
        self.setMinimumWidth(200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # --- 取值 ---------------------------------------------------------
    def value(self) -> float:
        return self._value

    def setValue(self, value: float, emit: bool = False):
        value = max(self._min, min(self._max, float(value)))
        if abs(value - self._value) < 1e-9:
            return
        self._value = value
        self.update()
        if emit:
            self.value_changed.emit(value)

    def _track_rect(self) -> QRect:
        return self.rect().adjusted(self.SIDE_MARGIN, 0, -self.SIDE_MARGIN, 0)

    def _db_at(self, x: float) -> float:
        track = self._track_rect()
        width = max(1, track.width())
        ratio = (x - track.left()) / width
        ratio = max(0.0, min(1.0, ratio))
        return self._min + ratio * (self._max - self._min)

    def _x_of(self, value: float) -> float:
        track = self._track_rect()
        ratio = (value - self._min) / (self._max - self._min) if self._max > self._min else 0.5
        return track.left() + ratio * track.width()

    # --- 事件 ---------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._dragging = True
        self.setValue(self._db_at(event.position().x()), emit=True)

    def mouseMoveEvent(self, event):
        if self._dragging:
            # 不做任何量化：鼠标在哪，dB 就是哪，数值框显示两位小数
            self.setValue(self._db_at(event.position().x()), emit=True)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.setValue(self._db_at(event.position().x()), emit=True)
            self.released.emit()

    def wheelEvent(self, event):
        step = 0.1 if event.angleDelta().y() > 0 else -0.1
        self.setValue(self._value + step, emit=True)
        self.released.emit()

    def keyPressEvent(self, event):
        step = {Qt.Key.Key_Left: -0.1, Qt.Key.Key_Down: -0.1,
                Qt.Key.Key_Right: 0.1, Qt.Key.Key_Up: 0.1,
                Qt.Key.Key_PageDown: -1.0, Qt.Key.Key_PageUp: 1.0}
        if event.key() in step:
            self.setValue(self._value + step[event.key()], emit=True)
            self.released.emit()
            return
        super().keyPressEvent(event)

    # --- 绘制 ---------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = self._track_rect()
        mid_y = self.rect().center().y()
        # 置灰时用调色板的 Disabled 组，避免自绘控件看不出被禁用
        group = (self.palette().ColorGroup.Active if self.isEnabled()
                 else self.palette().ColorGroup.Disabled)
        palette = self.palette()
        groove = QColor(palette.color(group, palette.ColorRole.Mid))
        groove.setAlpha(160)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(groove)
        painter.drawRoundedRect(QRect(track.left(), mid_y - 2, track.width(), 4), 2, 2)

        # 已经走过的那一段用强调色填出来，一眼能看出增益方向
        zero_x = int(self._x_of(0.0))
        handle_x = int(self._x_of(self._value))
        accent = QColor(palette.color(group, palette.ColorRole.Highlight))
        if handle_x != zero_x:
            span = QRect(min(zero_x, handle_x), mid_y - 2, abs(handle_x - zero_x), 4)
            painter.setBrush(accent)
            painter.drawRoundedRect(span, 2, 2)

        # 只保留中心的 0 dB 刻度
        tick = QColor(palette.color(group, palette.ColorRole.Text))
        tick.setAlpha(170)
        painter.setPen(QPen(tick, 1))
        painter.drawLine(zero_x, mid_y - 8, zero_x, mid_y + 8)
        painter.drawText(QRect(zero_x - 12, mid_y + 7, 24, 14),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "0")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawEllipse(handle_x - self.HANDLE_RADIUS, mid_y - self.HANDLE_RADIUS,
                            self.HANDLE_RADIUS * 2, self.HANDLE_RADIUS * 2)


class OfbQtToneEditorDialog(QDialog):
    """裁剪 + 命名对话框；接受时提供 samples/start/end 与名称。"""

    def __init__(self, parent: QWidget | None, samples: np.ndarray,
                 file_name: str = "", display_name: str = "", pcm_duration: float | None = None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Custom prompt tone"))
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.samples = np.asarray(samples, dtype="<i2")
        self._tmp_files: list[Path] = []

        self.waveform = ToneWaveform(self.samples, self)

        self.start_box = QDoubleSpinBox(self)
        self.end_box = QDoubleSpinBox(self)
        for box in (self.start_box, self.end_box):
            box.setDecimals(2)
            box.setSingleStep(0.05)
            box.setSuffix(" s")
            box.setMaximum(round(self.samples.size / TONE_SAMPLE_RATE, 2))
        self.start_box.setValue(0.0)
        self.end_box.setValue(min(TONE_MAX_DURATION, round(pcm_duration or self.samples.size / TONE_SAMPLE_RATE, 2)))

        self.duration_label = QLabel(self)
        self.play_button = QPushButton(self.tr("Play"), self)

        # --- 响度增益 -------------------------------------------------
        self.gain_slider = GainSlider(GAIN_MIN_DB, GAIN_MAX_DB, self)
        self.gain_slider.setMinimumWidth(200)

        self.gain_box = QDoubleSpinBox(self)
        self.gain_box.setDecimals(2)
        self.gain_box.setSingleStep(0.1)
        self.gain_box.setRange(GAIN_MIN_DB, GAIN_MAX_DB)
        self.gain_box.setKeyboardTracking(False)   # 打字时不抢着生效，失焦/回车/按上下箭头才生效
        self.gain_box.setFixedWidth(84)

        # 单位放在框外，框内只有数字，和 x.xx dB 的观感一致
        self.gain_unit_label = QLabel("dB", self)

        self.auto_gain_check = QCheckBox(self.tr("Set to the best volume"), self)

        self.gain_hint = QLabel(self)

        gain_row = QHBoxLayout()
        gain_row.addWidget(self.gain_slider, 1)
        gain_row.addWidget(self.gain_box)
        gain_row.addWidget(self.gain_unit_label)
        gain_row.addSpacing(12)
        gain_row.addWidget(self.auto_gain_check)

        # 文件名决定落盘的 <name>.pcm；后缀固定显示在框外，输入框里只填主体
        self.file_edit = QLineEdit(file_name, self)
        self.file_suffix_label = QLabel(".pcm", self)
        file_row = QHBoxLayout()
        file_row.setContentsMargins(0, 0, 0, 0)
        file_row.addWidget(self.file_edit)
        file_row.addWidget(self.file_suffix_label)

        # 显示名：用户写什么就显示什么，不参与 i18n
        self.display_edit = QLineEdit(display_name, self)

        playback = QHBoxLayout()
        playback.addWidget(self.start_box)
        playback.addWidget(QLabel("→", self))
        playback.addWidget(self.end_box)
        playback.addWidget(self.play_button)
        playback.addWidget(self.duration_label)
        playback.addStretch(1)

        form = QFormLayout()
        form.addRow(self.tr("Start / end"), playback)
        form.addRow(self.tr("Volume"), gain_row)
        form.addRow(self.tr("File Name"), file_row)
        form.addRow(self.tr("Display Name"), self.display_edit)

        hint = QLabel(self.tr("Only the selected range is saved. The 192000-byte limit "
                              "is about 5.7 s at 16755 Hz."), self)
        hint.setWordWrap(True)
        self.gain_hint.setWordWrap(True)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        # Qt 自带的 OK/Cancel 文案取决于 qtbase 翻译包；这里统一走本应用 i18n
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("OK"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))

        layout = QVBoxLayout(self)
        layout.addWidget(self.waveform)
        layout.addLayout(form)
        layout.addWidget(self.gain_hint)
        layout.addWidget(hint)
        layout.addWidget(self.buttons)

        self.waveform.range_changed.connect(self._on_range_changed)
        self.start_box.valueChanged.connect(self._on_boxes_changed)
        self.end_box.valueChanged.connect(self._on_boxes_changed)
        self.play_button.clicked.connect(self._on_play)
        self.gain_slider.value_changed.connect(self._on_slider_moved)
        self.gain_slider.released.connect(self._on_gain_applied)
        self.gain_box.valueChanged.connect(self._on_box_gain_changed)
        self.gain_box.editingFinished.connect(self._on_gain_applied)
        self.auto_gain_check.toggled.connect(self._on_auto_toggled)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.auto_gain_check.setChecked(True)   # 默认等同旧行为：峰值归一到不爆电平
        self._on_range_changed(self.waveform.start, self.waveform.end)

    # --- 同步 ---------------------------------------------------------
    def _on_range_changed(self, start: int, end: int):
        for box, value in ((self.start_box, start), (self.end_box, end)):
            box.blockSignals(True)
            box.setValue(round(value / TONE_SAMPLE_RATE, 2))
            box.blockSignals(False)
        self.duration_label.setText(f"{(end - start) / TONE_SAMPLE_RATE:.2f} s")
        if self.auto_gain_check.isChecked():
            self._set_gain_controls(self._auto_gain_value(), from_auto=True)
        self._update_gain_hint()

    def _on_boxes_changed(self):
        start = int(self.start_box.value() * TONE_SAMPLE_RATE)
        end = int(self.end_box.value() * TONE_SAMPLE_RATE)
        self.waveform.set_range(start, end)

    # --- 响度增益 -----------------------------------------------------
    @property
    def auto_gain(self) -> bool:
        return self.auto_gain_check.isChecked()

    @property
    def gain_db(self) -> float:
        """当前生效的增益：自动模式下按选区峰值现算，手动模式下取数值框。"""
        if self.auto_gain:
            return self._auto_gain_value()
        return float(self.gain_box.value())

    def _auto_gain_value(self) -> float:
        value = peak_gain_db(self.selection)
        return max(GAIN_MIN_DB, min(GAIN_MAX_DB, value))

    def _set_gain_controls(self, value: float, from_auto: bool = False):
        """把同一个值写进滑块与数值框；from_auto 时保留 0.01 dB 的余量在框里。"""
        self.gain_slider.setValue(value)
        self.gain_box.blockSignals(True)
        self.gain_box.setValue(round(value if from_auto else self.gain_slider.value(), 2))
        self.gain_box.blockSignals(False)
        self.waveform.set_gain(self.gain_slider.value())

    def _on_slider_moved(self, value: float):
        """拖动过程中：数值框跟随、波形按新电平实时重画（拖动结束才改动预览文件）。"""
        self.gain_box.blockSignals(True)
        self.gain_box.setValue(round(value, 2))
        self.gain_box.blockSignals(False)
        self.waveform.set_gain(value)
        self._update_gain_hint()

    def _on_box_gain_changed(self, value: float):
        self.gain_slider.setValue(value)
        self._on_gain_applied()   # 上下箭头点一下就生效，不用等失焦

    def _on_auto_toggled(self, checked: bool):
        if checked:
            # 勾选：算最佳增益并回填（滑块、数值框、波形三者一起更新）
            self._set_gain_controls(self._auto_gain_value(), from_auto=True)
        self.gain_slider.setEnabled(not checked)
        self.gain_box.setEnabled(not checked)
        self.gain_slider.update()   # 置灰后强制重绘，避免看起来「没变化」
        self.gain_box.update()
        # 取消勾选时保留当前（最佳）值，不回滚到勾选前的值
        self._update_gain_hint()
        self.waveform.set_gain(self.gain_db)
        self._restart_preview_if_playing()

    def _on_gain_applied(self):
        """手势结束/失焦/箭头：立即生效——重写预览音频，正在播就按新电平重播。"""
        if self.auto_gain:
            self._set_gain_controls(self._auto_gain_value(), from_auto=True)
        self.waveform.set_gain(self.gain_db)
        self._update_gain_hint()
        self._restart_preview_if_playing()

    def _update_gain_hint(self):
        gain = self.gain_db
        chunk = self.selection.astype(np.int32)
        peak = int(np.max(np.abs(chunk))) if chunk.size else 0
        if self.auto_gain:
            # 自动模式把「最佳增益」的依据摊开写：峰值多少、抬到了多少，避免看起来像没生效
            applied = int(round(peak * (10.0 ** (gain / 20.0)))) if peak else 0
            # 「更改为」不区分正负：正增益是抬、负增益是压，同一个说法都不会说反
            self.gain_hint.setText(self.tr("Best gain {0} dB — peak {1} changed to {2}.")
                                   .format(f"{gain:+.2f}", peak, applied))
            self.gain_hint.setStyleSheet("color: palette(mid);")
            return
        # 手动增益把峰值推过满响度（严格大于 26213）才提示；正好等于不算超
        over = peak > 0 and round(peak * (10.0 ** (gain / 20.0))) > TONE_FULL_SCALE
        if over:
            self.gain_hint.setText(self.tr("Exceeds full loudness, the signal may clip."))
            self.gain_hint.setStyleSheet("color: #d9534f;")
        else:
            self.gain_hint.clear()
            self.gain_hint.setStyleSheet("")

    # --- 播放 ---------------------------------------------------------
    def processed(self, samples: np.ndarray | None = None) -> np.ndarray:
        """按当前增益处理过、可直接保存/试听的样本（自动模式等于峰值归一）。"""
        chunk = self.selection if samples is None else samples
        return apply_gain_db(chunk, self.gain_db)

    def _selection_wav(self) -> Path:
        chunk = self.processed()
        fd, tmp_name = tempfile.mkstemp(suffix=".wav", prefix="ofb_preview_")
        os.close(fd)
        fd_path = Path(tmp_name)
        self._tmp_files.append(fd_path)
        with wave.open(str(fd_path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(TONE_SAMPLE_RATE)
            w.writeframes(chunk.tobytes())
        return fd_path

    def _restart_preview_if_playing(self):
        """增益改了又正在播：按新电平重放一遍，保证听到的就是要保存的。"""
        player = getattr(self, "_player", None)
        if player is None:
            return
        from PyQt6.QtMultimedia import QMediaPlayer
        if player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            return
        player.stop()
        player.setSource(QUrl())
        self._discard_previews()
        player.setSource(QUrl.fromLocalFile(str(self._selection_wav())))
        player.play()

    def _on_play(self):
        try:
            from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
        except ImportError:
            self.play_button.setEnabled(False)
            return
        if not hasattr(self, "_player"):
            self._player = QMediaPlayer(self)
            self._output = QAudioOutput(self)
            self._player.setAudioOutput(self._output)
            self._player.playbackStateChanged.connect(self._on_state)
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.stop()
            return
        # 先释放上一段预览文件（Windows 上媒体后端会锁住文件），再写新的一段
        self._player.stop()
        self._player.setSource(QUrl())
        self._discard_previews()
        self._player.setSource(QUrl.fromLocalFile(str(self._selection_wav())))
        self._player.play()

    def _discard_previews(self):
        """删掉已经不再被播放器引用的临时预览文件；删不掉就留给系统临时目录。"""
        for path in self._tmp_files:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        self._tmp_files.clear()

    def _on_state(self, state):
        self.play_button.setText(
            self.tr("Pause") if state == self._player.PlaybackState.PlayingState else self.tr("Play"))

    # --- 结果 ---------------------------------------------------------
    def cleanup(self):
        if hasattr(self, "_player"):
            self._player.stop()
            self._player.setSource(QUrl())   # 释放文件句柄，否则 unlink 会 WinError 32
        self._discard_previews()

    @property
    def selection(self) -> np.ndarray:
        return self.samples[self.waveform.start:self.waveform.end]

    @property
    def file_name(self) -> str:
        """文件名主体（不含 .pcm）。"""
        return self.file_edit.text().strip()

    @property
    def display_name(self) -> str:
        return self.display_edit.text().strip()
