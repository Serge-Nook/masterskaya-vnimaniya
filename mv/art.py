"""Векторные рисунки предметов. Каждая функция рисует в квадрате 0..100."""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF

from mv import theme

OUTLINE = QColor("#2E3D44")


def _pen(p: QPainter, width: float = 3.0, color: QColor = OUTLINE) -> None:
    pen = QPen(color, width)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)


def _fill(p: QPainter, color) -> None:
    p.setBrush(QBrush(QColor(color)))


def poly(*pts) -> QPolygonF:
    return QPolygonF([QPointF(x, y) for x, y in pts])


def star_path(cx: float, cy: float, r_out: float, r_in: float, n: int = 5) -> QPainterPath:
    path = QPainterPath()
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = -math.pi / 2 + i * math.pi / n
        pt = QPointF(cx + r * math.cos(a), cy + r * math.sin(a))
        path.moveTo(pt) if i == 0 else path.lineTo(pt)
    path.closeSubpath()
    return path


def heart_path(cx: float, cy: float, s: float) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(cx, cy + s * 0.9)
    path.cubicTo(cx - s * 1.4, cy, cx - s * 0.9, cy - s * 1.1, cx, cy - s * 0.45)
    path.cubicTo(cx + s * 0.9, cy - s * 1.1, cx + s * 1.4, cy, cx, cy + s * 0.9)
    return path


# --- предметы -------------------------------------------------------------

def cat(p, c):
    c = c or QColor("#E7A35C")
    _pen(p)
    _fill(p, c)
    p.drawPolygon(poly((24, 40), (28, 12), (44, 30)))
    p.drawPolygon(poly((76, 40), (72, 12), (56, 30)))
    p.drawEllipse(QRectF(20, 22, 60, 56))
    _fill(p, "#2E3D44")
    p.drawEllipse(QRectF(36, 42, 7, 9))
    p.drawEllipse(QRectF(57, 42, 7, 9))
    _fill(p, "#E88FB0")
    p.drawPolygon(poly((46, 56), (54, 56), (50, 61)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    _pen(p, 2)
    for dy in (-3, 3):
        p.drawLine(QPointF(40, 60 + dy), QPointF(18, 58 + dy * 2))
        p.drawLine(QPointF(60, 60 + dy), QPointF(82, 58 + dy * 2))
    p.drawArc(QRectF(43, 58, 7, 6), 180 * 16, 180 * 16)
    p.drawArc(QRectF(50, 58, 7, 6), 180 * 16, 180 * 16)


def star(p, c):
    _pen(p)
    _fill(p, c or theme.STAR)
    p.drawPath(star_path(50, 54, 42, 18))


def ball(p, c):
    c = QColor(c or theme.BLUE)
    _pen(p)
    _fill(p, c)
    p.drawEllipse(QRectF(12, 12, 76, 76))
    _fill(p, "white")
    path = QPainterPath()
    path.moveTo(14, 46)
    path.cubicTo(35, 36, 65, 36, 86, 46)
    path.lineTo(86, 56)
    path.cubicTo(65, 46, 35, 46, 14, 56)
    path.closeSubpath()
    p.drawPath(path)


def apple(p, c):
    _pen(p)
    _fill(p, c or theme.RED)
    path = QPainterPath()
    path.moveTo(50, 30)
    path.cubicTo(20, 10, 4, 50, 22, 76)
    path.cubicTo(32, 92, 44, 88, 50, 84)
    path.cubicTo(56, 88, 68, 92, 78, 76)
    path.cubicTo(96, 50, 80, 10, 50, 30)
    p.drawPath(path)
    _fill(p, theme.GREEN)
    p.drawEllipse(QRectF(52, 10, 22, 12))
    p.drawLine(QPointF(50, 30), QPointF(48, 14))


def house(p, c):
    _pen(p)
    _fill(p, c or theme.SAND)
    p.drawRect(QRectF(20, 46, 60, 42))
    _fill(p, theme.RED)
    p.drawPolygon(poly((12, 50), (50, 14), (88, 50)))
    _fill(p, theme.BROWN)
    p.drawRect(QRectF(44, 62, 14, 26))
    _fill(p, theme.SKY)
    p.drawRect(QRectF(26, 56, 13, 12))
    p.drawRect(QRectF(64, 56, 11, 12))


def fish(p, c):
    _pen(p)
    _fill(p, c or theme.ORANGE)
    p.drawPolygon(poly((70, 50), (92, 30), (92, 70)))
    p.drawEllipse(QRectF(10, 28, 66, 44))
    _fill(p, "white")
    p.drawEllipse(QRectF(22, 40, 12, 12))
    _fill(p, "#2E3D44")
    p.drawEllipse(QRectF(26, 44, 5, 5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(40, 34, 18, 32), -60 * 16, 120 * 16)


def flower(p, c):
    _pen(p)
    _fill(p, theme.GREEN)
    p.drawRect(QRectF(47, 50, 6, 44))
    p.drawEllipse(QRectF(52, 66, 22, 10))
    _fill(p, c or theme.PINK)
    for i in range(6):
        a = i * math.pi / 3
        p.drawEllipse(QPointF(50 + 18 * math.cos(a), 34 + 18 * math.sin(a)), 13, 13)
    _fill(p, theme.YELLOW)
    p.drawEllipse(QPointF(50, 34), 12, 12)


def car(p, c):
    _pen(p)
    _fill(p, c or theme.BLUE)
    path = QPainterPath()
    path.moveTo(8, 70)
    path.lineTo(8, 52)
    path.lineTo(28, 50)
    path.lineTo(38, 30)
    path.lineTo(68, 30)
    path.lineTo(80, 50)
    path.lineTo(92, 54)
    path.lineTo(92, 70)
    path.closeSubpath()
    p.drawPath(path)
    _fill(p, theme.SKY)
    p.drawPolygon(poly((40, 36), (52, 36), (52, 50), (33, 50)))
    p.drawPolygon(poly((57, 36), (66, 36), (74, 50), (57, 50)))
    _fill(p, "#3A4A50")
    p.drawEllipse(QPointF(28, 72), 10, 10)
    p.drawEllipse(QPointF(72, 72), 10, 10)


def sun(p, c):
    _pen(p)
    _fill(p, c or theme.YELLOW)
    for i in range(10):
        a = i * math.pi / 5
        p.drawLine(QPointF(50 + 30 * math.cos(a), 50 + 30 * math.sin(a)),
                   QPointF(50 + 44 * math.cos(a), 50 + 44 * math.sin(a)))
    p.drawEllipse(QPointF(50, 50), 25, 25)


def tree(p, c):
    _pen(p)
    _fill(p, theme.BROWN)
    p.drawRect(QRectF(44, 76, 12, 18))
    _fill(p, c or QColor("#4E9A5B"))
    p.drawPolygon(poly((50, 6), (24, 40), (76, 40)))
    p.drawPolygon(poly((50, 24), (16, 60), (84, 60)))
    p.drawPolygon(poly((50, 42), (10, 80), (90, 80)))


def heart(p, c):
    _pen(p)
    _fill(p, c or theme.RED)
    p.drawPath(heart_path(50, 50, 36))


def bell(p, c):
    _pen(p)
    _fill(p, c or theme.YELLOW)
    path = QPainterPath()
    path.moveTo(18, 78)
    path.cubicTo(26, 70, 26, 56, 28, 42)
    path.cubicTo(30, 18, 70, 18, 72, 42)
    path.cubicTo(74, 56, 74, 70, 82, 78)
    path.closeSubpath()
    p.drawPath(path)
    p.drawEllipse(QPointF(50, 84), 7, 7)
    p.drawEllipse(QPointF(50, 16), 5, 5)


def key(p, c):
    _pen(p)
    _fill(p, c or theme.STAR)
    p.drawEllipse(QPointF(30, 50), 18, 18)
    p.drawRect(QRectF(46, 45, 42, 10))
    p.drawRect(QRectF(70, 55, 7, 12))
    p.drawRect(QRectF(81, 55, 7, 9))
    _fill(p, theme.PANEL)
    p.drawEllipse(QPointF(30, 50), 7, 7)


def door(p, c):
    _pen(p)
    _fill(p, c or theme.BROWN)
    path = QPainterPath()
    path.moveTo(22, 94)
    path.lineTo(22, 30)
    path.arcTo(QRectF(22, 6, 56, 48), 180, -180)
    path.lineTo(78, 94)
    path.closeSubpath()
    p.drawPath(path)
    _fill(p, theme.STAR)
    p.drawEllipse(QPointF(66, 60), 5, 5)


def chest(p, c):
    _pen(p)
    _fill(p, c or theme.BROWN)
    p.drawRect(QRectF(12, 44, 76, 42))
    p.drawChord(QRectF(12, 20, 76, 48), 0, 180 * 16)
    _fill(p, theme.STAR)
    p.drawRect(QRectF(44, 46, 12, 16))


def album(p, c):
    _pen(p)
    _fill(p, c or QColor("#F7F3E8"))
    p.drawRect(QRectF(10, 22, 80, 60))
    _fill(p, theme.SKY)
    p.drawRect(QRectF(18, 30, 64, 44))
    _fill(p, theme.YELLOW)
    p.drawEllipse(QPointF(68, 42), 6, 6)
    _fill(p, theme.GREEN)
    p.drawPolygon(poly((18, 74), (40, 48), (60, 74)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for x in range(16, 90, 8):
        p.drawEllipse(QPointF(x, 18), 3, 3)


def pencils(p, c):
    colors = [theme.RED, theme.YELLOW, theme.BLUE, theme.GREEN]
    for i, col in enumerate(colors):
        p.save()
        p.translate(26 + i * 16, 50)
        p.rotate(-8 + i * 5)
        _pen(p)
        _fill(p, col)
        p.drawRect(QRectF(-6, -34, 12, 54))
        _fill(p, theme.SAND)
        p.drawPolygon(poly((-6, 20), (6, 20), (0, 36)))
        p.restore()


def brush(p, c):
    p.save()
    p.translate(50, 50)
    p.rotate(-35)
    _pen(p)
    _fill(p, c or theme.RED)
    p.drawRect(QRectF(-5, -44, 10, 56))
    _fill(p, theme.GREY)
    p.drawRect(QRectF(-7, 12, 14, 12))
    _fill(p, "#5A3E2B")
    path = QPainterPath()
    path.moveTo(-7, 24)
    path.cubicTo(-10, 36, -2, 44, 0, 46)
    path.cubicTo(2, 44, 10, 36, 7, 24)
    path.closeSubpath()
    p.drawPath(path)
    p.restore()


def paints(p, c):
    _pen(p)
    _fill(p, "white")
    p.drawRoundedRect(QRectF(8, 26, 84, 48), 8, 8)
    for i, col in enumerate([theme.RED, theme.YELLOW, theme.GREEN, theme.BLUE, theme.PURPLE, theme.ORANGE]):
        _fill(p, col)
        p.drawEllipse(QRectF(14 + (i % 3) * 26, 31 + (i // 3) * 21, 20, 17))


def eraser(p, c):
    p.save()
    p.translate(50, 50)
    p.rotate(-20)
    _pen(p)
    _fill(p, c or theme.PINK)
    p.drawRoundedRect(QRectF(-38, -16, 48, 32), 6, 6)
    _fill(p, theme.BLUE)
    p.drawRoundedRect(QRectF(10, -16, 28, 32), 6, 6)
    p.restore()


def ruler(p, c):
    p.save()
    p.translate(50, 50)
    p.rotate(-30)
    _pen(p)
    _fill(p, c or theme.YELLOW)
    p.drawRect(QRectF(-44, -12, 88, 24))
    for i in range(9):
        x = -38 + i * 9.5
        p.drawLine(QPointF(x, -12), QPointF(x, -12 + (10 if i % 2 == 0 else 6)))
    p.restore()


def book(p, c):
    _pen(p)
    _fill(p, c or theme.GREEN)
    p.drawRect(QRectF(22, 12, 58, 76))
    _fill(p, "#F7F3E8")
    p.drawRect(QRectF(76, 16, 8, 70))
    _fill(p, theme.YELLOW)
    p.drawRect(QRectF(34, 26, 34, 14))


def notebook(p, c):
    _pen(p)
    _fill(p, c or theme.BLUE)
    p.drawRect(QRectF(24, 10, 56, 80))
    _fill(p, "white")
    p.drawRect(QRectF(36, 26, 34, 14))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for y in range(18, 86, 10):
        p.drawEllipse(QPointF(24, y), 3, 3)


def glue(p, c):
    _pen(p)
    _fill(p, c or QColor("#F7F3E8"))
    p.drawRoundedRect(QRectF(32, 28, 36, 62), 6, 6)
    _fill(p, theme.PURPLE)
    p.drawRect(QRectF(36, 12, 28, 18))
    _fill(p, theme.YELLOW)
    p.drawRect(QRectF(36, 46, 28, 20))


def scissors(p, c):
    _pen(p, 4)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(40, 60), QPointF(84, 14))
    p.drawLine(QPointF(60, 60), QPointF(16, 14))
    _fill(p, c or theme.ORANGE)
    p.drawEllipse(QPointF(32, 72), 13, 13)
    p.drawEllipse(QPointF(68, 72), 13, 13)
    _fill(p, theme.BG)
    p.drawEllipse(QPointF(32, 72), 6, 6)
    p.drawEllipse(QPointF(68, 72), 6, 6)


def pen(p, c):
    p.save()
    p.translate(50, 50)
    p.rotate(-40)
    _pen(p)
    _fill(p, c or theme.BLUE)
    p.drawRect(QRectF(-6, -40, 12, 64))
    _fill(p, "#F7F3E8")
    p.drawPolygon(poly((-6, 24), (6, 24), (0, 40)))
    _fill(p, "#2E3D44")
    p.drawRect(QRectF(-8, -40, 16, 12))
    p.restore()


def paper(p, c):
    _pen(p)
    for i, col in enumerate([theme.YELLOW, theme.GREEN, theme.BLUE, theme.RED]):
        _fill(p, col)
        p.drawRect(QRectF(14 + i * 7, 14 + i * 7, 54, 62))


def teddy(p, c):
    _pen(p)
    _fill(p, c or theme.BROWN)
    p.drawEllipse(QPointF(30, 22), 10, 10)
    p.drawEllipse(QPointF(70, 22), 10, 10)
    p.drawEllipse(QRectF(26, 50, 48, 44))
    p.drawEllipse(QRectF(28, 14, 44, 40))
    _fill(p, theme.SAND)
    p.drawEllipse(QRectF(40, 34, 20, 16))
    _fill(p, "#2E3D44")
    p.drawEllipse(QPointF(41, 30), 3, 3)
    p.drawEllipse(QPointF(59, 30), 3, 3)
    p.drawEllipse(QPointF(50, 39), 4, 3)


def candy(p, c):
    _pen(p)
    _fill(p, c or theme.PINK)
    p.drawPolygon(poly((30, 50), (10, 34), (10, 66)))
    p.drawPolygon(poly((70, 50), (90, 34), (90, 66)))
    p.drawEllipse(QRectF(28, 34, 44, 32))


def pyramid(p, c):
    _pen(p)
    _fill(p, theme.BROWN)
    p.drawRect(QRectF(47, 12, 6, 74))
    for i, col in enumerate([theme.RED, theme.ORANGE, theme.YELLOW, theme.GREEN, theme.BLUE]):
        w = 70 - i * 12
        _fill(p, col)
        p.drawRoundedRect(QRectF(50 - w / 2, 76 - i * 13, w, 13), 6, 6)
    _fill(p, theme.PURPLE)
    p.drawRect(QRectF(16, 86, 68, 8))


def dice(p, c):
    _pen(p)
    _fill(p, c or "white")
    p.drawRoundedRect(QRectF(18, 18, 64, 64), 10, 10)
    _fill(p, "#2E3D44")
    for x, y in ((34, 34), (66, 66), (50, 50), (66, 34), (34, 66)):
        p.drawEllipse(QPointF(x, y), 5, 5)


def balloon(p, c):
    _pen(p)
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(50, 74)
    path.cubicTo(42, 82, 58, 88, 50, 98)
    p.drawPath(path)
    _fill(p, c or theme.RED)
    p.drawEllipse(QRectF(24, 6, 52, 64))
    p.drawPolygon(poly((50, 68), (44, 76), (56, 76)))


def circle(p, c):
    _pen(p)
    _fill(p, c or theme.RED)
    p.drawEllipse(QRectF(8, 8, 84, 84))


def square(p, c):
    _pen(p)
    _fill(p, c)
    p.drawRoundedRect(QRectF(12, 12, 76, 76), 8, 8)


def triangle(p, c):
    _pen(p)
    _fill(p, c)
    p.drawPolygon(poly((50, 8), (92, 88), (8, 88)))


def backpack(p, c):
    _pen(p)
    _fill(p, c or theme.ACCENT)
    p.drawRoundedRect(QRectF(16, 20, 68, 74), 16, 16)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(34, 4, 32, 30), 0, 180 * 16)
    _fill(p, theme.ACCENT_LIGHT)
    p.drawRoundedRect(QRectF(26, 50, 48, 32), 10, 10)
    _fill(p, theme.STAR)
    p.drawRect(QRectF(46, 46, 8, 10))


def hedgehog(p, c):
    _pen(p)
    _fill(p, c or QColor("#8A6A55"))
    spikes = QPainterPath()
    spikes.moveTo(14, 70)
    for i in range(9):
        a = math.pi * (1 - i / 8)
        spikes.lineTo(52 + 40 * math.cos(a - 0.17), 66 - 40 * math.sin(a - 0.17))
        spikes.lineTo(52 + 30 * math.cos(a - 0.34), 66 - 30 * math.sin(a - 0.34))
    spikes.lineTo(88, 72)
    spikes.closeSubpath()
    p.drawPath(spikes)
    _fill(p, theme.SAND)
    p.drawEllipse(QRectF(56, 44, 36, 30))
    _fill(p, "#2E3D44")
    p.drawEllipse(QPointF(80, 54), 3, 3)
    p.drawEllipse(QPointF(92, 60), 4, 4)


def rainbow(p, c):
    p.setBrush(Qt.BrushStyle.NoBrush)
    for i, col in enumerate([theme.RED, theme.ORANGE, theme.YELLOW, theme.GREEN, theme.BLUE, theme.PURPLE]):
        pen = QPen(col, 7)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        r = 44 - i * 7
        p.drawArc(QRectF(50 - r, 76 - r, 2 * r, 2 * r), 0, 180 * 16)
    _pen(p)
    _fill(p, "white")
    p.drawEllipse(QPointF(16, 76), 12, 10)
    p.drawEllipse(QPointF(84, 76), 12, 10)


DRAW = {
    name: fn
    for name, fn in globals().items()
    if callable(fn) and getattr(fn, "__module__", "") == __name__ and fn.__code__.co_varnames[:2] == ("p", "c")
}

LISTEN_OBJECTS = ["cat", "star", "ball", "apple", "house", "fish", "flower", "car", "sun", "tree", "heart", "bell"]
SCHOOL_ITEMS = ["album", "pencils", "brush", "paints", "eraser", "ruler", "book", "notebook", "glue", "scissors", "pen", "paper"]
TOYS = ["car", "ball", "teddy", "candy", "pyramid", "dice", "balloon", "fish"]


def draw(p: QPainter, name: str, rect: QRectF, color=None, opacity: float = 1.0) -> None:
    fn = DRAW.get(name)
    if fn is None:
        return
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setOpacity(p.opacity() * opacity)
    side = min(rect.width(), rect.height())
    p.translate(rect.center().x() - side / 2, rect.center().y() - side / 2)
    p.scale(side / 100.0, side / 100.0)
    fn(p, QColor(color) if color is not None else None)
    p.restore()
