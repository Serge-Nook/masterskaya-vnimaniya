"""Енот Тихон — анимированный наставник (векторная 2D-анимация)."""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from mv import art, theme

STATES = ("greet", "explain", "praise", "retry", "think", "breathe", "joy", "bye")

FUR = QColor("#8F9BA1")
FUR_DARK = QColor("#5D686E")
FUR_LIGHT = QColor("#E9E6DF")
MASK = QColor("#2F3A40")
INK = QColor("#25313A")


class Tikhon(QWidget):
    def __init__(self, parent=None, state: str = "greet"):
        super().__init__(parent)
        self.state = state
        self.speaking = False
        self.breath = 0.0
        self._t0 = time.monotonic()
        self._state_t0 = self._t0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(160, 190)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

    def sizeHint(self) -> QSize:
        return QSize(320, 380)

    def set_state(self, state: str) -> None:
        if state in STATES and state != self.state:
            self.state = state
            self._state_t0 = time.monotonic()

    def set_speaking(self, value: bool) -> None:
        self.speaking = value

    def set_breath(self, value: float) -> None:
        self.breath = max(0.0, min(1.0, value))

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)

    def showEvent(self, e):
        self.timer.start(16)
        super().showEvent(e)

    # ------------------------------------------------------------------
    def paintEvent(self, _):
        t = time.monotonic() - self._t0
        st = time.monotonic() - self._state_t0
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = min(self.width() / 200.0, self.height() / 240.0)
        p.translate((self.width() - 200 * scale) / 2, (self.height() - 240 * scale) / 2)
        p.scale(scale, scale)
        draw_tikhon(p, self.state, t, st, self.speaking, self.breath)
        p.end()


def _pen(p, w=2.4, c=INK):
    pen = QPen(c, w)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)


def _arm(p: QPainter, shoulder: QPointF, angle: float, length: float = 44) -> QPointF:
    p.save()
    p.translate(shoulder)
    p.rotate(angle)
    _pen(p)
    p.setBrush(FUR)
    p.drawRoundedRect(QRectF(-9, 0, 18, length), 9, 9)
    p.setBrush(MASK)
    p.drawEllipse(QPointF(0, length), 10, 9)
    p.restore()
    a = math.radians(angle)
    return QPointF(shoulder.x() - math.sin(a) * length, shoulder.y() + math.cos(a) * length)


def draw_tikhon(p: QPainter, state: str, t: float, st: float, speaking: bool, breath: float) -> None:
    slow = math.sin(t * 1.3)
    hop = 0.0
    if state == "joy":
        hop = -abs(math.sin(t * 3.2)) * 12
    elif state == "praise":
        hop = -abs(math.sin(t * 2.4)) * 5
    breathe_scale = 1.0 + (0.07 * breath if state == "breathe" else 0.012 * math.sin(t * 1.6))
    tilt = {"retry": 7.0, "think": -6.0}.get(state, 0.0) + (1.5 * slow if state != "breathe" else 0)

    p.save()
    p.translate(0, hop)

    # хвост
    p.save()
    p.translate(140, 200)
    p.rotate(-25 + 9 * math.sin(t * 1.1))
    for i in range(6):
        _pen(p)
        p.setBrush(MASK if i % 2 else FUR)
        p.drawEllipse(QRectF(-4 + i * 9, -16 - i * 6, 26, 24))
    p.restore()

    # ноги
    _pen(p)
    p.setBrush(MASK)
    p.drawEllipse(QRectF(68, 214, 26, 16))
    p.drawEllipse(QRectF(106, 214, 26, 16))

    # тело
    p.save()
    p.translate(100, 222)
    p.scale(breathe_scale, breathe_scale)
    p.translate(-100, -222)
    _pen(p)
    p.setBrush(FUR)
    p.drawEllipse(QRectF(58, 118, 84, 104))
    p.setBrush(FUR_LIGHT)
    p.drawEllipse(QRectF(74, 140, 52, 72))
    p.restore()

    # лапы
    ls, rs = QPointF(66, 140), QPointF(134, 140)
    if state in ("greet", "bye"):
        _arm(p, ls, 18)
        _arm(p, rs, -128 + 18 * math.sin(t * 3.0))
    elif state == "explain":
        _arm(p, ls, 18)
        _arm(p, rs, -95 + 12 * math.sin(t * 1.8))
    elif state == "praise":
        _arm(p, ls, 160 - 8 * math.sin(t * 2.4))
        _arm(p, rs, -160 + 8 * math.sin(t * 2.4))
    elif state == "retry":
        _arm(p, ls, 18)
        hand = _arm(p, rs, -70 + 4 * slow)
        p.save()
        _pen(p, 2, QColor(theme.FOCUS))
        p.setBrush(Qt.BrushStyle.NoBrush)
        r = 8 + 4 * (0.5 + 0.5 * math.sin(t * 3))
        p.drawEllipse(QPointF(hand.x() + 14, hand.y() - 4), r, r)
        p.restore()
    elif state == "think":
        _arm(p, ls, 18)
        _arm(p, rs, 168)
    elif state == "breathe":
        _arm(p, ls, 35 + 30 * breath)
        _arm(p, rs, -35 - 30 * breath)
    elif state == "joy":
        _arm(p, ls, 150 + 14 * math.sin(t * 3.2))
        _arm(p, rs, -150 - 14 * math.sin(t * 3.2))
    else:
        _arm(p, ls, 18)
        _arm(p, rs, -18)

    # голова
    p.save()
    p.translate(100, 124)
    p.rotate(tilt)
    p.translate(-100, -124)
    _draw_head(p, state, t, speaking)
    p.restore()

    p.restore()

    # дополнительные эффекты
    if state == "think":
        _pen(p, 2)
        p.setBrush(theme.PANEL)
        for i in range(3):
            phase = (t * 0.8 + i * 0.33) % 1.0
            p.setOpacity(0.35 + 0.65 * phase)
            p.drawEllipse(QPointF(150 + i * 12, 40 - i * 12), 4 + i * 2, 4 + i * 2)
        p.setOpacity(1.0)
    elif state in ("joy", "praise"):
        for i in range(4):
            a = t * 0.9 + i * math.pi / 2
            x = 100 + 86 * math.cos(a)
            y = 110 + 70 * math.sin(a) * 0.6 + hop
            p.setOpacity(0.5 + 0.5 * math.sin(t * 2 + i))
            p.save()
            p.translate(x - 9, y - 9)
            p.scale(0.18, 0.18)
            _pen(p, 6)
            p.setBrush(theme.STAR)
            p.drawPath(art.star_path(50, 50, 50, 22))
            p.restore()
        p.setOpacity(1.0)


def _draw_head(p: QPainter, state: str, t: float, speaking: bool) -> None:
    _pen(p)
    # уши
    for sx in (1, -1):
        p.save()
        p.translate(100 + sx * 40, 40)
        p.rotate(sx * 24)
        p.setBrush(FUR)
        p.drawEllipse(QRectF(-17, -22, 34, 40))
        p.setBrush(MASK)
        p.drawEllipse(QRectF(-9, -13, 18, 24))
        p.restore()
    # голова
    p.setBrush(FUR)
    p.drawEllipse(QRectF(42, 30, 116, 100))
    # светлая морда
    p.setBrush(FUR_LIGHT)
    muzzle = QPainterPath()
    muzzle.moveTo(54, 86)
    muzzle.cubicTo(60, 60, 140, 60, 146, 86)
    muzzle.cubicTo(140, 122, 60, 122, 54, 86)
    p.drawPath(muzzle)
    p.drawEllipse(QRectF(80, 36, 40, 30))
    # маска «бандита»
    p.setBrush(MASK)
    mask = QPainterPath()
    mask.moveTo(48, 72)
    mask.cubicTo(52, 52, 84, 54, 96, 74)
    mask.cubicTo(98, 78, 102, 78, 104, 74)
    mask.cubicTo(116, 54, 148, 52, 152, 72)
    mask.cubicTo(150, 94, 120, 96, 106, 84)
    mask.cubicTo(102, 82, 98, 82, 94, 84)
    mask.cubicTo(80, 96, 50, 94, 48, 72)
    p.drawPath(mask)
    # глаза
    blink = (t % 4.2) < 0.14
    closed = state == "breathe" or blink
    look_up = -3 if state == "think" else 0
    for cx in (76, 124):
        if closed:
            _pen(p, 3, QColor("white"))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(cx - 9, 70, 18, 10), 200 * 16, 140 * 16)
            _pen(p)
        else:
            p.setBrush(QColor("white"))
            _pen(p, 1.5)
            p.drawEllipse(QPointF(cx, 74), 10, 11)
            p.setBrush(INK)
            p.drawEllipse(QPointF(cx + (2 if state == "think" else 0), 75 + look_up), 6, 7)
            p.setBrush(QColor("white"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx + 2, 72 + look_up), 2, 2)
            _pen(p)
    # нос
    p.setBrush(INK)
    p.drawEllipse(QRectF(91, 88, 18, 12))
    # рот
    open_amt = (0.5 + 0.5 * math.sin(t * 14)) * 7 if speaking else 0
    _pen(p, 2.4)
    if state == "retry":
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(88, 98, 24, 12), 200 * 16, 140 * 16)
    elif open_amt > 1 or state in ("joy", "praise", "greet"):
        h = max(open_amt, 6 if state in ("joy", "praise") else 3)
        p.setBrush(QColor("#9E4A54"))
        p.drawChord(QRectF(88, 98 - h / 2, 24, 8 + h), 180 * 16, 180 * 16)
    else:
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(86, 96, 14, 10), 180 * 16, 180 * 16)
        p.drawArc(QRectF(100, 96, 14, 10), 180 * 16, 180 * 16)
    # румянец
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(232, 143, 176, 90))
    p.drawEllipse(QPointF(62, 98), 8, 5)
    p.drawEllipse(QPointF(138, 98), 8, 5)
