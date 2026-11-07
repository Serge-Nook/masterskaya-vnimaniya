"""Генератор картинок-сцен (пул из 60 сцен) для «Что изменилось?» и пазлов."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter

from mv import art, theme

POOL_SIZE = 60
SCENE_OBJECTS = [
    "cat", "star", "ball", "apple", "house", "fish", "flower", "car", "sun", "tree", "heart", "bell",
    "teddy", "pyramid", "balloon", "book", "key", "chest", "candy", "dice",
]
RECOLOR = {"ball", "flower", "car", "balloon", "book", "heart", "candy", "fish"}
BACKGROUNDS = ["meadow", "room", "sea", "evening"]
COLORS = [theme.RED, theme.BLUE, theme.GREEN, theme.YELLOW, theme.PURPLE, theme.ORANGE, theme.PINK]


@dataclass
class Item:
    name: str
    color: QColor | None
    rect: QRectF


@dataclass
class Scene:
    background: str
    items: list[Item] = field(default_factory=list)
    slots: list[QRectF] = field(default_factory=list)

    def paint(self, p: QPainter, area: QRectF) -> None:
        p.save()
        p.translate(area.topLeft())
        p.scale(area.width() / 1280.0, area.height() / 640.0)
        paint_background(p, self.background)
        for it in self.items:
            art.draw(p, it.name, it.rect, it.color)
        p.restore()


@dataclass
class Change:
    kind: str
    rect: QRectF


def paint_background(p: QPainter, kind: str) -> None:
    full = QRectF(0, 0, 1280, 640)
    p.setPen(Qt.PenStyle.NoPen)
    if kind == "meadow":
        g = QLinearGradient(QPointF(0, 0), QPointF(0, 640))
        g.setColorAt(0, QColor("#D6ECF5"))
        g.setColorAt(0.55, QColor("#EAF5F8"))
        g.setColorAt(0.56, QColor("#C9E2B4"))
        g.setColorAt(1, QColor("#B2D59C"))
        p.fillRect(full, g)
    elif kind == "room":
        p.fillRect(QRectF(0, 0, 1280, 380), QColor("#F3E9D8"))
        p.fillRect(QRectF(0, 380, 1280, 260), QColor("#E1CBA8"))
        p.setBrush(QColor("#EADCC4"))
        for x in range(0, 1280, 160):
            p.drawRect(QRectF(x, 0, 80, 380))
    elif kind == "sea":
        g = QLinearGradient(QPointF(0, 0), QPointF(0, 640))
        g.setColorAt(0, QColor("#CDE8F2"))
        g.setColorAt(0.45, QColor("#A8D4E6"))
        g.setColorAt(0.75, QColor("#8EC3DA"))
        g.setColorAt(0.76, QColor("#F1E2BE"))
        g.setColorAt(1, QColor("#E8D3A6"))
        p.fillRect(full, g)
    else:
        g = QLinearGradient(QPointF(0, 0), QPointF(0, 640))
        g.setColorAt(0, QColor("#E5DDF0"))
        g.setColorAt(0.6, QColor("#F4E6DA"))
        g.setColorAt(0.61, QColor("#CFE0C3"))
        g.setColorAt(1, QColor("#BBD3AC"))
        p.fillRect(full, g)


def _slots(rng: random.Random) -> list[QRectF]:
    slots = []
    cols, rows = 5, 2
    cw, ch = 1280 / cols, 640 / rows
    for r in range(rows):
        for c in range(cols):
            size = 150
            x = c * cw + (cw - size) / 2 + rng.uniform(-18, 18)
            y = r * ch + (ch - size) / 2 + rng.uniform(-14, 14)
            slots.append(QRectF(x, y, size, size))
    return slots


def make_scene(seed: int, n_objects: int, rng: random.Random | None = None) -> Scene:
    """Сцена №seed из пула (детерминированная). Показывается n первых предметов."""
    base = random.Random(seed * 7919 + 17)
    slots = _slots(base)
    names = base.sample(SCENE_OBJECTS, 10)
    colors = [base.choice(COLORS) if n in RECOLOR else None for n in names]
    order = list(range(10))
    base.shuffle(order)
    scene = Scene(background=BACKGROUNDS[seed % len(BACKGROUNDS)], slots=slots)
    used = sorted(order[: max(1, min(9, n_objects))])
    for i in used:
        scene.items.append(Item(names[i], colors[i], QRectF(slots[i])))
    return scene


def clone(scene: Scene) -> Scene:
    return Scene(
        background=scene.background,
        items=[Item(it.name, QColor(it.color) if it.color is not None else None, QRectF(it.rect)) for it in scene.items],
        slots=[QRectF(s) for s in scene.slots],
    )


def make_change(scene: Scene, rng: random.Random, allow_move: bool = False) -> tuple[Scene, Change]:
    changed = clone(scene)
    free = [s for s in scene.slots if all(not s.intersects(it.rect) for it in scene.items)]
    kinds = ["color", "remove", "replace", "add"]
    if allow_move and free:
        kinds.append("move")
    rng.shuffle(kinds)
    for kind in kinds:
        if kind == "color":
            candidates = [i for i, it in enumerate(changed.items) if it.name in RECOLOR]
            if not candidates:
                continue
            i = rng.choice(candidates)
            it = changed.items[i]
            it.color = rng.choice([c for c in COLORS if it.color is None or c.name() != it.color.name()])
            return changed, Change(kind, QRectF(it.rect))
        if kind == "remove" and len(changed.items) > 2:
            i = rng.randrange(len(changed.items))
            it = changed.items.pop(i)
            return changed, Change(kind, QRectF(it.rect))
        if kind == "replace":
            i = rng.randrange(len(changed.items))
            present = {it.name for it in changed.items}
            options = [n for n in SCENE_OBJECTS if n not in present]
            it = changed.items[i]
            it.name = rng.choice(options)
            it.color = rng.choice(COLORS) if it.name in RECOLOR else None
            return changed, Change(kind, QRectF(it.rect))
        if kind == "add" and free:
            slot = rng.choice(free)
            present = {it.name for it in changed.items}
            name = rng.choice([n for n in SCENE_OBJECTS if n not in present])
            changed.items.append(Item(name, rng.choice(COLORS) if name in RECOLOR else None, QRectF(slot)))
            return changed, Change(kind, QRectF(slot))
        if kind == "move" and free:
            i = rng.randrange(len(changed.items))
            slot = rng.choice(free)
            it = changed.items[i]
            it.rect = QRectF(slot)
            return changed, Change(kind, QRectF(slot))
    it = changed.items[0]
    it.name = "star" if it.name != "star" else "heart"
    it.color = None
    return changed, Change("replace", QRectF(it.rect))
