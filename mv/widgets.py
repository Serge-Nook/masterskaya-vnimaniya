from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from mv import art, theme
from mv.tikhon import Tikhon


class Screen(QWidget):
    """Базовый экран. back() вызывается по Esc / кнопке B."""

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setObjectName("Root")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def on_enter(self) -> None:
        pass

    def on_leave(self) -> None:
        pass

    def back(self) -> None:
        pass

    def first_focus(self):
        buttons = [b for b in self.findChildren(QPushButton) if b.isVisible() and b.isEnabled()]
        return buttons[0] if buttons else None


class PictureButton(QPushButton):
    """Крупная кнопка-карточка с векторной картинкой и подписью."""

    def __init__(self, text: str, picture: str | None = None, color=None, parent=None, big: bool = True):
        super().__init__(parent)
        self.label = text
        self.picture = picture
        self.color = QColor(color) if color else theme.PANEL
        self.big = big
        self.badge = ""
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(QSize(180, 160) if big else QSize(120, 110))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def sizeHint(self) -> QSize:
        return QSize(260, 240) if self.big else QSize(160, 140)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        bg = QColor(self.color)
        if self.isDown():
            bg = bg.darker(108)
        p.setPen(QPen(theme.FOCUS if self.hasFocus() else theme.ACCENT_LIGHT, 6 if self.hasFocus() else 3))
        p.setBrush(bg)
        p.drawRoundedRect(r, 26, 26)
        text_h = 58 if self.big else 42
        if self.picture:
            pic = QRectF(r.left() + 14, r.top() + 12, r.width() - 28, r.height() - text_h - 18)
            art.draw(p, self.picture, pic)
        f = QFont(self.font())
        size = 30 if self.big else 22
        f.setWeight(QFont.Weight.ExtraBold)
        while size > 16:
            f.setPixelSize(size)
            if QFontMetrics(f).horizontalAdvance(self.label) <= r.width() - 20:
                break
            size -= 2
        p.setFont(f)
        p.setPen(theme.INK)
        p.drawText(QRectF(r.left() + 8, r.bottom() - text_h - 4, r.width() - 16, text_h),
                   Qt.AlignmentFlag.AlignCenter, self.label)
        if self.badge:
            f.setPixelSize(20)
            p.setFont(f)
            p.drawText(r.adjusted(0, 10, -18, 0), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, self.badge)
        p.end()


def make_button(text: str, primary: bool = False, slot=None) -> QPushButton:
    b = QPushButton(text)
    if primary:
        b.setObjectName("Primary")
    b.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if slot:
        b.clicked.connect(slot)
    return b


class Hourglass(QWidget):
    """Песочные часы: показывают, сколько осталось от занятия."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fraction = 1.0
        self.setFixedSize(54, 70)
        self.setToolTip("")

    def set_fraction(self, value: float) -> None:
        value = max(0.0, min(1.0, value))
        if abs(value - self.fraction) > 0.002:
            self.fraction = value
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(QPen(theme.BROWN, 4))
        p.drawLine(QPointF(6, 4), QPointF(w - 6, 4))
        p.drawLine(QPointF(6, h - 4), QPointF(w - 6, h - 4))
        glass = QPainterPath()
        glass.moveTo(10, 8)
        glass.lineTo(w - 10, 8)
        glass.lineTo(w / 2 + 4, h / 2)
        glass.lineTo(w - 10, h - 8)
        glass.lineTo(10, h - 8)
        glass.lineTo(w / 2 - 4, h / 2)
        glass.closeSubpath()
        p.setPen(QPen(theme.INK_SOFT, 2.5))
        p.setBrush(QColor(255, 255, 255, 170))
        p.drawPath(glass)
        p.setClipPath(glass)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.STAR)
        top_h = (h / 2 - 10) * self.fraction
        p.drawRect(QRectF(0, h / 2 - top_h, w, top_h))
        bottom_h = (h / 2 - 10) * (1 - self.fraction)
        p.drawRect(QRectF(0, h - 8 - bottom_h, w, bottom_h))
        if 0 < self.fraction < 1:
            p.drawRect(QRectF(w / 2 - 1.5, h / 2, 3, h / 2 - 8))
        p.end()


class StarCounter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.count = 0
        self.setFixedHeight(56)
        self.setMinimumWidth(130)

    def set_count(self, n: int) -> None:
        self.count = n
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        art.draw(p, "star", QRectF(4, 4, 48, 48))
        f = QFont(self.font())
        f.setPixelSize(30)
        f.setWeight(QFont.Weight.ExtraBold)
        p.setFont(f)
        p.setPen(theme.INK)
        p.drawText(QRectF(58, 0, self.width() - 58, self.height()), Qt.AlignmentFlag.AlignVCenter, str(self.count))
        p.end()


class StarsRow(QWidget):
    """Звёздочки за уровень (0..3) с мягким появлением."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stars = 0
        self.phase = 0.0
        self.setFixedHeight(110)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def show_stars(self, n: int) -> None:
        self.stars = n
        self.phase = 0.0
        self.timer.start(16)

    def _tick(self):
        self.phase += 0.016 / 1.2
        if self.phase >= self.stars + 0.5:
            self.timer.stop()
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = 96
        total = 3 * size + 2 * 20
        x0 = (self.width() - total) / 2
        for i in range(3):
            rect = QRectF(x0 + i * (size + 20), 7, size, size)
            if i < self.stars:
                k = max(0.0, min(1.0, self.phase - i))
                k = 1 - (1 - k) ** 3
                s = size * (0.4 + 0.6 * k)
                art.draw(p, "star", QRectF(rect.center().x() - s / 2, rect.center().y() - s / 2, s, s), opacity=k)
            else:
                art.draw(p, "star", rect, color=QColor("#DDE5E1"))
        p.end()


class Bubble(QLabel):
    """Облачко с репликой (субтитры)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(
            "QLabel { background: #FBFAF5; border: 3px solid #A9CBB7; border-radius: 26px;"
            " padding: 18px 26px; font-size: 32px; font-weight: 700; color: #23343B; }"
        )


class TikhonPanel(QWidget):
    """Тихон + облачко-субтитры + кнопки «Повторить» и «Дальше»."""

    proceed = Signal()

    def __init__(self, ctx, parent=None, next_text: str = ""):
        super().__init__(parent)
        from mv.i18n import tr

        self.ctx = ctx
        self.keys: list[str] = []
        self.tikhon = Tikhon(self)
        self.bubble = Bubble(self)
        self.repeat = make_button(tr("Повторить"), slot=self.replay)
        self.next = make_button(next_text or tr("Дальше"), primary=True, slot=self.proceed.emit)
        self.extra = QVBoxLayout()

        right = QVBoxLayout()
        right.addStretch(1)
        right.addWidget(self.bubble)
        right.addSpacing(16)
        right.addLayout(self.extra)
        right.addSpacing(16)
        row = QHBoxLayout()
        row.addWidget(self.repeat)
        row.addStretch(1)
        row.addWidget(self.next)
        right.addLayout(row)
        right.addStretch(1)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.addWidget(self.tikhon, 4)
        lay.addSpacing(20)
        lay.addLayout(right, 6)
        ctx.audio.speaking.connect(self._speaking)

    def say(self, keys, state: str = "explain") -> None:
        from mv.audio import phrase_text

        self.keys = [keys] if isinstance(keys, str) else list(keys)
        self.tikhon.set_state(state)
        self.bubble.setText(phrase_text(self.keys))
        self.ctx.audio.say(self.keys)

    def replay(self) -> None:
        if self.keys:
            self.ctx.audio.say(self.keys)

    def _speaking(self, on: bool) -> None:
        if self.isVisible():
            self.tikhon.set_speaking(on)


class Pointer(QWidget):
    """Виртуальный указатель для геймпада (левый/правый стик)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.pos_f = QPointF(200, 200)
        self.active = False
        self.hide()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("white"), 7))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(self.pos_f, 22, 22)
        p.setPen(QPen(theme.FOCUS, 4))
        p.drawEllipse(self.pos_f, 22, 22)
        p.setBrush(theme.FOCUS)
        p.drawEllipse(self.pos_f, 4, 4)
        p.end()


def ease(x: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))
