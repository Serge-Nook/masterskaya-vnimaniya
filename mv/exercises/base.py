from __future__ import annotations

import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QTransform
from PySide6.QtWidgets import QSizePolicy, QWidget

from mv import theme
from mv.db import LevelResult

W, H = 1280.0, 640.0


class Exercise(QWidget):
    """Базовый класс упражнения: виртуальный холст 1280×640, масштабируется под экран."""

    key = ""
    workshop = ""
    title = ""
    picture = "star"
    intro: list[str] = []
    animated = True
    show_tikhon_between = True

    done = Signal(object)

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.level = 1
        self.difficulty = 2
        self.hint = False
        self.rng = random.Random()
        self.started = 0.0
        self.finished = False
        self.err_impulsive = self.err_sequence = self.err_omission = 0
        self.reactions: list[float] = []
        self._xf = QTransform()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self._last = time.monotonic()

    # API для хоста
    @classmethod
    def intro_keys(cls, level: int) -> list[str]:
        return list(cls.intro)

    def actions(self) -> list[tuple[str, object]]:
        return []

    def start(self, level: int, difficulty: int, hint: bool = False, seed: int | None = None) -> None:
        self.level, self.difficulty, self.hint = level, difficulty, hint
        self.rng = random.Random(seed)
        self.err_impulsive = self.err_sequence = self.err_omission = 0
        self.reactions = []
        self.finished = False
        self.started = time.monotonic()
        self.setup()
        self._last = time.monotonic()
        if self.animated:
            self.timer.start(16)
        self.update()

    def stop(self) -> None:
        self.timer.stop()
        self.finished = True
        self.unlisten_audio()

    def listen_audio(self, slot) -> None:
        """Подписка на окончание реплики (не более одной одновременно)."""
        self.unlisten_audio()
        self._audio_slot = slot
        self.ctx.audio.finished.connect(slot)

    def unlisten_audio(self) -> None:
        slot = getattr(self, "_audio_slot", None)
        if slot is not None:
            self._audio_slot = None
            self.ctx.audio.finished.disconnect(slot)

    @property
    def power(self) -> int:
        """Эффективная сложность 1..12 с учётом настройки взрослого."""
        return max(1, min(12, self.level + (self.difficulty - 2) * 2))

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self.started) * 1000)

    def finish(self, success: bool, stars: int | None = None) -> None:
        if self.finished:
            return
        self.stop()
        errors = self.err_impulsive + self.err_sequence + self.err_omission
        if stars is None:
            stars = 0 if not success else (3 if errors == 0 else 2 if errors <= 2 else 1)
        result = LevelResult(
            success=success, stars=stars, duration_ms=self.elapsed_ms(),
            err_impulsive=self.err_impulsive, err_sequence=self.err_sequence,
            err_omission=self.err_omission, reactions=list(self.reactions),
        )
        QTimer.singleShot(450, lambda: self.done.emit(result))

    # переопределяемые
    def setup(self) -> None:
        pass

    def tick(self, dt: float) -> None:
        pass

    def paint(self, p: QPainter) -> None:
        pass

    def press(self, pt: QPointF) -> None:
        pass

    def move(self, pt: QPointF, pressed: bool) -> None:
        pass

    def release(self, pt: QPointF) -> None:
        pass

    def on_key(self, key: int) -> bool:
        return False

    # служебное
    def _tick(self) -> None:
        now = time.monotonic()
        dt = min(0.05, now - self._last)
        self._last = now
        if not self.finished:
            try:
                self.tick(dt)
            except Exception:
                self.timer.stop()
                raise
        self.update()

    def _transform(self) -> QTransform:
        s = min(self.width() / W, self.height() / H)
        xf = QTransform()
        xf.translate((self.width() - W * s) / 2, (self.height() - H * s) / 2)
        xf.scale(s, s)
        return xf

    def to_scene(self, pos) -> QPointF:
        inv, _ = self._xf.inverted()
        return inv.map(QPointF(pos))

    def paintEvent(self, _):
        self._xf = self._transform()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), theme.BG)
        p.setTransform(self._xf)
        p.setClipRect(QRectF(0, 0, W, H))
        self.paint(p)
        p.end()

    def resizeEvent(self, e):
        self._xf = self._transform()
        super().resizeEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and not self.finished:
            self.press(self.to_scene(e.position()))

    def mouseMoveEvent(self, e):
        if not self.finished:
            self.move(self.to_scene(e.position()), bool(e.buttons() & Qt.MouseButton.LeftButton))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and not self.finished:
            self.release(self.to_scene(e.position()))

    def keyPressEvent(self, e):
        if not self.finished and self.on_key(e.key()):
            e.accept()
            return
        super().keyPressEvent(e)

    # рисование
    def text(self, p: QPainter, rect: QRectF, text: str, size: int = 34, color=None, bold: bool = True,
             align=Qt.AlignmentFlag.AlignCenter) -> None:
        f = QFont(self.font())
        f.setPixelSize(size)
        f.setWeight(QFont.Weight.ExtraBold if bold else QFont.Weight.Normal)
        p.setFont(f)
        p.setPen(QColor(color) if color is not None else theme.INK)
        p.drawText(rect, int(align) | int(Qt.TextFlag.TextWordWrap), text)

    def panel(self, p: QPainter, rect: QRectF, color=None, radius: float = 26) -> None:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(color) if color is not None else theme.PANEL)
        p.drawRoundedRect(rect, radius, radius)
