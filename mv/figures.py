"""Человечек для карточек разминки (медленная, предсказуемая анимация)."""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from mv import theme

BODY = QColor("#5E8C74")
SKIN = QColor("#F3D2B5")


def _limb(p, a: QPointF, b: QPointF, w=14):
    pen = QPen(BODY, w)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.drawLine(a, b)


def _pt(origin: QPointF, length: float, deg: float) -> QPointF:
    r = math.radians(deg)
    return QPointF(origin.x() + length * math.sin(r), origin.y() + length * math.cos(r))


def draw_pose(p: QPainter, pose: str, rect: QRectF, t: float) -> None:
    p.save()
    s = min(rect.width(), rect.height()) / 300.0
    p.translate(rect.center().x() - 150 * s, rect.top())
    p.scale(s, s)
    w = 0.5 - 0.5 * math.cos(t * 1.6)  # 0..1, плавно
    hip = QPointF(150, 190)
    neck = QPointF(150, 100)
    arm_l, arm_r, leg_l, leg_r = 160.0, 200.0, 10.0, -10.0
    dy = 0.0
    rot = 0.0
    if pose == "wu_stretch":
        arm_l, arm_r = 180 - 10 * w, 180 + 10 * w
        dy = -8 * w
    elif pose == "wu_jump":
        dy = -30 * abs(math.sin(t * 2.4))
        arm_l, arm_r = 140, 220
    elif pose == "wu_clap":
        arm_l, arm_r = 150 + 20 * w, 210 - 20 * w
    elif pose == "wu_squat":
        dy = 40 * w
        arm_l, arm_r = 100, 260
        leg_l, leg_r = 10 + 40 * w, -10 - 40 * w
    elif pose == "wu_turn":
        rot = 0
        arm_l, arm_r = 90, 270
    elif pose == "wu_shake":
        arm_l = 40 + 12 * math.sin(t * 9)
        arm_r = -40 - 12 * math.sin(t * 9)
    elif pose == "wu_stand":
        leg_r = -70
        arm_l, arm_r = 100, 260
    elif pose == "wu_shoulders":
        arm_l, arm_r = 25, -25
        dy = -4 * math.sin(t * 3)
    p.translate(0, dy)
    if pose == "wu_turn":
        p.translate(150, 0)
        p.scale(math.cos(t * 1.2), 1)
        p.translate(-150, 0)
    if pose == "wu_stand":
        _limb(p, hip, _pt(hip, 90, leg_l))
        knee = _pt(hip, 50, leg_r)
        _limb(p, hip, knee)
        _limb(p, knee, _pt(knee, 45, 10))
    elif pose == "wu_squat":
        for ang in (leg_l, leg_r):
            knee = _pt(hip, 50, ang * 1.4)
            _limb(p, hip, knee)
            _limb(p, knee, QPointF(knee.x() * 0.6 + hip.x() * 0.4, 280 - dy))
    else:
        _limb(p, hip, _pt(hip, 95, leg_l))
        _limb(p, hip, _pt(hip, 95, leg_r))
    _limb(p, neck, hip, 34)
    _limb(p, neck, _pt(neck, 80, arm_l))
    _limb(p, neck, _pt(neck, 80, arm_r))
    p.setPen(QPen(theme.INK, 3))
    p.setBrush(SKIN)
    p.drawEllipse(QPointF(150, 62), 34, 34)
    p.setBrush(theme.INK)
    p.drawEllipse(QPointF(138, 58), 4, 4)
    p.drawEllipse(QPointF(162, 58), 4, 4)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(136, 62, 28, 18), 200 * 16, 140 * 16)
    p.restore()
