"""Мастерская 2 — «Усидчивость и планирование»."""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from mv import art, theme
from mv.exercises.base import H, W, Exercise
from mv.i18n import N_, tr
from mv.scenes import make_scene


def generate_maze(cols: int, rows: int, rng) -> dict[tuple[int, int], set[tuple[int, int]]]:
    """Идеальный лабиринт (DFS). Возвращает для каждой клетки множество открытых соседей."""
    links: dict[tuple[int, int], set[tuple[int, int]]] = {(c, r): set() for c in range(cols) for r in range(rows)}
    stack = [(0, 0)]
    seen = {(0, 0)}
    while stack:
        c, r = stack[-1]
        nbrs = [(c + dc, r + dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= c + dc < cols and 0 <= r + dr < rows and (c + dc, r + dr) not in seen]
        if not nbrs:
            stack.pop()
            continue
        nxt = rng.choice(nbrs)
        links[(c, r)].add(nxt)
        links[nxt].add((c, r))
        seen.add(nxt)
        stack.append(nxt)
    return links


def bfs_path(links, start, goal) -> list[tuple[int, int]]:
    prev = {start: None}
    queue = [start]
    while queue:
        cur = queue.pop(0)
        if cur == goal:
            break
        for n in links[cur]:
            if n not in prev:
                prev[n] = cur
                queue.append(n)
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
    return path[::-1]


class PlanMixin:
    """Показ плана перед выполнением: карточки шагов."""

    def paint_plan(self, p: QPainter, steps: list[tuple[str, str]], current: int, area: QRectF, big: bool) -> None:
        n = len(steps)
        size = area.height() - 20 if not big else min(220, area.width() / n - 60)
        gap = 70 if big else 40
        total = n * size + (n - 1) * gap
        x = area.center().x() - total / 2
        y = area.top() + (area.height() - size) / 2 - (24 if big else 0)
        for i, (pic, label) in enumerate(steps):
            rect = QRectF(x + i * (size + gap), y, size, size)
            done = i < current
            self.panel(p, rect, theme.ACCENT_LIGHT if done else theme.PANEL, 18)
            if i == current:
                p.setPen(QPen(theme.FOCUS, 5))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(rect, 18, 18)
            art.draw(p, pic, rect.adjusted(size * 0.18, size * 0.12, -size * 0.18, -size * 0.24), opacity=0.5 if done else 1)
            self.text(p, QRectF(rect.left(), rect.bottom() - size * 0.26, size, size * 0.24), str(i + 1), int(size * 0.18))
            if big:
                self.text(p, QRectF(rect.left() - 30, rect.bottom() + 6, size + 60, 50), label, 28)
            if i < n - 1:
                ax = rect.right() + gap / 2
                ay = rect.center().y()
                p.setPen(QPen(theme.INK_SOFT, 5 if big else 3))
                p.drawLine(QPointF(ax - gap * 0.3, ay), QPointF(ax + gap * 0.3, ay))
                p.drawLine(QPointF(ax + gap * 0.3, ay), QPointF(ax + gap * 0.1, ay - gap * 0.18))
                p.drawLine(QPointF(ax + gap * 0.3, ay), QPointF(ax + gap * 0.1, ay + gap * 0.18))


class Maze(PlanMixin, Exercise):
    key = "maze"
    workshop = "planning"
    title = N_("Лабиринт")
    picture = "key"
    intro = ["intro_maze"]

    def setup(self):
        pw = self.power
        self.cols = min(14, 5 + pw)
        self.rows = min(8, 3 + (pw + 1) // 2)
        self.links = generate_maze(self.cols, self.rows, self.rng)
        cells = [(c, r) for c in range(self.cols) for r in range(self.rows)]
        self.start_cell = (0, 0)
        goal = (self.cols - 1, self.rows - 1)
        far = sorted(cells, key=lambda x: -len(bfs_path(self.links, self.start_cell, x)))
        n_steps = 2 if pw <= 5 else 3
        picks = []
        candidates = [c for c in far if c not in (self.start_cell, goal)]
        self.rng.shuffle(candidates)
        for c in candidates:
            if all(abs(c[0] - q[0]) + abs(c[1] - q[1]) > 2 for q in picks):
                picks.append(c)
            if len(picks) == n_steps - 1:
                break
        if n_steps == 3:
            names = [("apple", tr("Яблоко")), ("key", tr("Ключик")), ("house", tr("Домик"))]
        else:
            names = [("key", tr("Ключик")), ("house", tr("Домик"))]
        self.targets = list(zip(picks + [goal], names))
        self.plan = [n for _, n in self.targets]
        self.collected = 0
        self.pos = self.start_cell
        self.anim_from = self.pos
        self.anim_t = 1.0
        self.phase = "plan"
        self.plan_until = time.monotonic() + (4.0 if not self.hint else 6.0)
        self.bump = 0.0
        self.warn_until = 0.0
        self.hint_path: list[tuple[int, int]] = []
        self.moves = 0

    def actions(self):
        return [(tr("Показать план"), self._show_plan)]

    def _show_plan(self):
        if self.phase == "play":
            self.phase = "plan"
            self.plan_until = time.monotonic() + 3.0

    def _geom(self):
        top = 92
        cs = min((W - 80) / self.cols, (H - top - 20) / self.rows)
        ox = (W - cs * self.cols) / 2
        oy = top + (H - top - 20 - cs * self.rows) / 2
        return cs, ox, oy

    def cell_rect(self, c, r):
        cs, ox, oy = self._geom()
        return QRectF(ox + c * cs, oy + r * cs, cs, cs)

    def tick(self, dt):
        if self.phase == "plan" and time.monotonic() >= self.plan_until:
            self.phase = "play"
            if self.hint and self.collected == 0:
                self.hint_path = bfs_path(self.links, self.pos, self.targets[0][0])
                self.hint_until = time.monotonic() + 2.5
        self.anim_t = min(1.0, self.anim_t + dt * 7)
        self.bump = max(0.0, self.bump - dt * 3)

    def step(self, dc, dr):
        if self.phase == "plan":
            self.phase = "play"
            return
        if self.anim_t < 1.0:
            return
        nxt = (self.pos[0] + dc, self.pos[1] + dr)
        if nxt not in self.links[self.pos]:
            self.bump = 1.0
            return
        self.anim_from, self.pos, self.anim_t = self.pos, nxt, 0.0
        self.moves += 1
        self.ctx.audio.sfx("step")
        for i, (cell, _) in enumerate(self.targets):
            if cell == nxt and i >= self.collected:
                if i == self.collected:
                    self.collected += 1
                    self.ctx.audio.sfx("pop")
                    if self.collected == len(self.targets):
                        self.finish(True)
                else:
                    self.err_sequence += 1
                    self.warn_until = time.monotonic() + 2.0
                    self.ctx.audio.say("plan_order")

    def on_key(self, key):
        d = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0), Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}.get(key)
        if d:
            self.step(*d)
            return True
        return False

    def press(self, pt):
        if self.phase == "plan":
            self.phase = "play"
            return
        cur = self.cell_rect(*self.pos).center()
        dx, dy = pt.x() - cur.x(), pt.y() - cur.y()
        cs = self._geom()[0]
        if math.hypot(dx, dy) < cs * 0.4:
            return
        if abs(dx) > abs(dy):
            self.step(1 if dx > 0 else -1, 0)
        else:
            self.step(0, 1 if dy > 0 else -1)

    def paint(self, p):
        self.panel(p, QRectF(0, 0, W, H), theme.BG_DEEP, 0)
        if self.phase == "plan":
            self.text(p, QRectF(0, 20, W, 60), tr("План"), 44)
            self.paint_plan(p, self.plan, self.collected, QRectF(40, 90, W - 80, H - 160), True)
            self.text(p, QRectF(0, H - 70, W, 60), tr("Нажми, когда запомнишь"), 26, theme.INK_SOFT, False)
            return
        self.paint_plan(p, self.plan, self.collected, QRectF(20, 10, 80 * len(self.plan) + 80, 72), False)
        cs, ox, oy = self._geom()
        self.panel(p, QRectF(ox - 8, oy - 8, cs * self.cols + 16, cs * self.rows + 16), theme.PANEL, 14)
        if self.hint_path and time.monotonic() < getattr(self, "hint_until", 0):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(224, 160, 53, 80))
            for c in self.hint_path:
                p.drawRoundedRect(self.cell_rect(*c).adjusted(cs * 0.2, cs * 0.2, -cs * 0.2, -cs * 0.2), 8, 8)
        pen = QPen(theme.ACCENT, max(4.0, cs * 0.09))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for c in range(self.cols):
            for r in range(self.rows):
                rect = self.cell_rect(c, r)
                if (c + 1, r) not in self.links[(c, r)]:
                    p.drawLine(rect.topRight(), rect.bottomRight())
                if (c, r + 1) not in self.links[(c, r)]:
                    p.drawLine(rect.bottomLeft(), rect.bottomRight())
                if c == 0:
                    p.drawLine(rect.topLeft(), rect.bottomLeft())
                if r == 0:
                    p.drawLine(rect.topLeft(), rect.topRight())
        for i, (cell, (pic, _)) in enumerate(self.targets):
            if i < self.collected:
                continue
            art.draw(p, pic, self.cell_rect(*cell).adjusted(cs * 0.14, cs * 0.14, -cs * 0.14, -cs * 0.14),
                     opacity=1.0 if i == self.collected else 0.6)
        a = self.cell_rect(*self.anim_from).center()
        b = self.cell_rect(*self.pos).center()
        k = 1 - (1 - self.anim_t) ** 2
        x = a.x() + (b.x() - a.x()) * k + math.sin(self.bump * 18) * 5 * self.bump
        y = a.y() + (b.y() - a.y()) * k
        art.draw(p, "hedgehog", QRectF(x - cs * 0.42, y - cs * 0.42, cs * 0.84, cs * 0.84))
        if time.monotonic() < self.warn_until:
            self.panel(p, QRectF(W / 2 - 360, H - 96, 720, 80))
            self.text(p, QRectF(W / 2 - 360, H - 96, 720, 80), tr("Сначала — шаг по плану"), 32)


class Puzzle(PlanMixin, Exercise):
    key = "puzzle"
    workshop = "planning"
    title = N_("Пазл")
    picture = "dice"
    intro = ["intro_puzzle"]

    def setup(self):
        pw = self.power
        self.rows = 2 if pw <= 7 else 3
        self.cols = 2 if pw <= 3 else 3 if pw <= 9 else 4
        self.scene = make_scene(self.rng.randrange(60), 6 + pw // 3, self.rng)
        self.board = QRectF(40, 70, 640, 520)
        n = self.rows * self.cols
        order = list(range(n))
        while order == sorted(order) and n > 1:
            self.rng.shuffle(order)
        self.tray = order
        self.placed: set[int] = set()
        self.selected: int | None = None
        self.phase = "plan"
        self.plan_until = time.monotonic() + (5.0 if self.hint else 3.5)
        self.shake: tuple[int, float] | None = None
        self.warn_until = 0.0
        self.drag: QPointF | None = None
        self.plan_steps = [("sun", tr("Посмотри")), ("star", tr("Верх")), ("tree", tr("Низ"))]

    def actions(self):
        return [(tr("Посмотреть картинку"), self._peek)]

    def _peek(self):
        self.phase = "plan"
        self.plan_until = time.monotonic() + 2.5

    def piece_src(self, idx) -> QRectF:
        r, c = divmod(idx, self.cols)
        return QRectF(c * 1280 / self.cols, r * 640 / self.rows, 1280 / self.cols, 640 / self.rows)

    def slot_rect(self, idx) -> QRectF:
        r, c = divmod(idx, self.cols)
        w, h = self.board.width() / self.cols, self.board.height() / self.rows
        return QRectF(self.board.left() + c * w, self.board.top() + r * h, w, h)

    def tray_rects(self):
        items = [i for i in self.tray if i not in self.placed]
        cols = 2 if len(items) > 4 else 2
        pw = (W - 760) / cols - 20
        ph = pw * (640 / self.rows) / (1280 / self.cols)
        ph = min(ph, 150)
        pw = ph * (1280 / self.cols) / (640 / self.rows)
        rects = []
        for k, idx in enumerate(items):
            c, r = k % cols, k // cols
            rects.append((idx, QRectF(740 + c * (pw + 20), 80 + r * (ph + 18), pw, ph)))
        return rects

    def tick(self, dt):
        if self.phase == "plan" and time.monotonic() >= self.plan_until:
            self.phase = "play"

    def _draw_piece(self, p, idx, rect):
        src = self.piece_src(idx)
        p.save()
        p.setClipRect(rect)
        p.translate(rect.left(), rect.top())
        p.scale(rect.width() / src.width(), rect.height() / src.height())
        p.translate(-src.left(), -src.top())
        self.scene.paint(p, QRectF(0, 0, 1280, 640))
        p.restore()
        p.setPen(QPen(theme.INK_SOFT, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(rect)

    def paint(self, p):
        self.panel(p, QRectF(0, 0, W, H), theme.BG_DEEP, 0)
        if self.phase == "plan":
            self.scene.paint(p, QRectF(140, 30, 1000, 500))
            self.paint_plan(p, self.plan_steps, 0, QRectF(0, 540, W, 90), False)
            return
        self.paint_plan(p, self.plan_steps, 1 if self.top_done() is False else 2, QRectF(20, 4, 400, 60), False)
        self.panel(p, self.board.adjusted(-10, -10, 10, 10), theme.PANEL, 12)
        for idx in range(self.rows * self.cols):
            rect = self.slot_rect(idx)
            if idx in self.placed:
                self._draw_piece(p, idx, rect)
            else:
                p.setPen(QPen(theme.ACCENT_LIGHT, 3, Qt.PenStyle.DashLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRect(rect.adjusted(4, 4, -4, -4))
                if self.hint:
                    p.setOpacity(0.18)
                    self._draw_piece(p, idx, rect)
                    p.setOpacity(1)
        now = time.monotonic()
        for idx, rect in self.tray_rects():
            if self.shake and self.shake[0] == idx and now < self.shake[1]:
                rect = rect.translated(math.sin(now * 40) * 8, 0)
            if self.selected == idx and self.drag is not None:
                continue
            self._draw_piece(p, idx, rect)
            if self.selected == idx:
                p.setPen(QPen(theme.FOCUS, 6))
                p.drawRect(rect.adjusted(-4, -4, 4, 4))
        if self.selected is not None and self.drag is not None:
            src = dict(self.tray_rects()).get(self.selected)
            if src:
                self._draw_piece(p, self.selected, QRectF(self.drag.x() - src.width() / 2, self.drag.y() - src.height() / 2,
                                                          src.width(), src.height()))
        if now < self.warn_until:
            self.panel(p, QRectF(W / 2 - 340, H - 92, 680, 76))
            self.text(p, QRectF(W / 2 - 340, H - 92, 680, 76), tr("Сначала собери верхний ряд"), 30)

    def top_done(self) -> bool:
        return all(i in self.placed for i in range(self.cols))

    def press(self, pt):
        if self.phase == "plan":
            self.phase = "play"
            return
        for idx, rect in self.tray_rects():
            if rect.contains(pt):
                self.selected = idx
                self.drag = None
                self.ctx.audio.sfx("tick")
                return
        if self.selected is not None:
            self._drop(pt)

    def move(self, pt, pressed):
        if pressed and self.selected is not None and self.phase == "play":
            self.drag = pt

    def release(self, pt):
        if self.drag is not None and self.selected is not None:
            self.drag = None
            if self.board.contains(pt):
                self._drop(pt)

    def _drop(self, pt):
        target = None
        for idx in range(self.rows * self.cols):
            if self.slot_rect(idx).contains(pt):
                target = idx
        if target is None or target in self.placed:
            return
        idx = self.selected
        if idx >= self.cols and not self.top_done():
            self.err_sequence += 1
            self.warn_until = time.monotonic() + 2.0
            self.shake = (idx, time.monotonic() + 0.5)
            self.ctx.audio.say("puzzle_top_first")
            self.selected = None
            return
        if target == idx:
            self.placed.add(idx)
            self.selected = None
            self.ctx.audio.sfx("pop")
            if len(self.placed) == self.rows * self.cols:
                self.finish(True)
        else:
            self.err_omission += 1
            self.shake = (idx, time.monotonic() + 0.5)
            self.ctx.audio.sfx("soft")
            self.selected = None


LESSONS = {
    "lesson_draw": ["album", "pencils", "brush", "paints", "eraser"],
    "lesson_math": ["notebook", "pen", "ruler", "pencils", "eraser"],
    "lesson_read": ["book", "notebook", "pen", "pencils"],
    "lesson_craft": ["paper", "glue", "scissors", "pencils", "album"],
}
ITEM_LABELS = {
    "album": N_("альбом"), "pencils": N_("карандаши"), "brush": N_("кисточка"), "paints": N_("краски"), "eraser": N_("ластик"),
    "ruler": N_("линейка"), "book": N_("книжка"), "notebook": N_("тетрадь"), "glue": N_("клей"), "scissors": N_("ножницы"),
    "pen": N_("ручка"), "paper": N_("цветная бумага"),
}


class Backpack(Exercise):
    key = "backpack"
    workshop = "planning"
    title = N_("Собери портфель")
    picture = "backpack"
    intro = ["intro_backpack"]

    def setup(self):
        pw = self.power
        self.lesson = self.rng.choice(list(LESSONS))
        need_n = 2 if pw <= 2 else 3 if pw <= 6 else 4
        self.needed = self.rng.sample(LESSONS[self.lesson], need_n)
        others = [i for i in ITEM_LABELS if i not in LESSONS[self.lesson]]
        toys = ["teddy", "candy", "pyramid", "dice", "balloon", "car", "ball"]
        n_school_distract = min(len(others), max(0, pw // 3))
        n_toys = min(len(toys), 2 + pw // 2)
        shelf = self.needed + self.rng.sample(others, n_school_distract) + self.rng.sample(toys, n_toys)
        self.rng.shuffle(shelf)
        self.shelf = shelf
        self.packed: list[str] = []
        self.shake: tuple[str, float] | None = None
        self.show_list_always = pw <= 4 or self.hint
        self.phase = "list"
        self.list_until = None
        self.ctx.audio.say([self.lesson, "pack_take"] + [f"acc_{n}" for n in self.needed])
        self.listen_audio(self._spoken)

    def _spoken(self):
        self.unlisten_audio()
        if self.phase == "list":
            self.list_until = time.monotonic() + 1.5

    def stop(self):
        super().stop()
        self.unlisten_audio()

    def actions(self):
        return [(tr("Список"), self._show_list), (tr("Готово"), self._done)]

    def _show_list(self):
        self.phase = "list"
        self.list_until = time.monotonic() + 3.0

    def _done(self):
        if self.phase != "play":
            return
        missing = [n for n in self.needed if n not in self.packed]
        if missing:
            self.err_omission += len(missing)
            self.ctx.audio.sfx("soft")
            self.missing_flash = time.monotonic() + 2.0
            if self.err_omission >= 3:
                self.finish(False)
            return
        self.finish(True)

    def tick(self, dt):
        if self.phase == "list" and self.list_until and time.monotonic() >= self.list_until:
            self.phase = "play"

    def shelf_rects(self):
        cols = min(6, max(4, math.ceil(len(self.shelf) / 2)))
        size = min(150, (W - 420) / cols - 18)
        out = []
        for i, name in enumerate(self.shelf):
            c, r = i % cols, i // cols
            out.append((name, QRectF(40 + c * (size + 18), 120 + r * (size + 40), size, size)))
        return out

    def paint(self, p):
        self.panel(p, QRectF(0, 0, W, H), theme.BG_DEEP, 0)
        title = tr({"lesson_draw": N_("Урок рисования"), "lesson_math": N_("Урок математики"),
                    "lesson_read": N_("Урок чтения"), "lesson_craft": N_("Урок труда")}[self.lesson])
        self.text(p, QRectF(30, 16, W - 420, 70), title, 40, align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if self.phase == "list":
            n = len(self.needed)
            size = 200
            x0 = W / 2 - (n * size + (n - 1) * 30) / 2
            for i, name in enumerate(self.needed):
                rect = QRectF(x0 + i * (size + 30), 170, size, size)
                self.panel(p, rect)
                art.draw(p, name, rect.adjusted(24, 20, -24, -20))
                self.text(p, QRectF(rect.left() - 20, rect.bottom() + 10, size + 40, 50), tr(ITEM_LABELS[name]), 28)
            self.text(p, QRectF(0, H - 80, W, 60), tr("Запомни, что нужно взять"), 28, theme.INK_SOFT, False)
            return
        now = time.monotonic()
        for name, rect in self.shelf_rects():
            if name in self.packed:
                continue
            if self.shake and self.shake[0] == name and now < self.shake[1]:
                rect = rect.translated(math.sin(now * 40) * 8, 0)
            self.panel(p, rect, theme.PANEL, 18)
            art.draw(p, name, rect.adjusted(14, 14, -14, -14))
        bag = QRectF(W - 360, 150, 320, 340)
        art.draw(p, "backpack", bag)
        for i, name in enumerate(self.packed):
            art.draw(p, name, QRectF(W - 350 + (i % 4) * 76, 510 + (i // 4) * 60, 66, 56))
        if self.show_list_always:
            for i, name in enumerate(self.needed):
                done = name in self.packed
                art.draw(p, name, QRectF(W - 360 + i * 80, 40, 70, 70), opacity=0.35 if done else 1)
        if now < getattr(self, "missing_flash", 0):
            self.panel(p, QRectF(140, H - 100, 700, 80))
            self.text(p, QRectF(140, H - 100, 700, 80), tr("Чего-то не хватает…"), 32)

    def press(self, pt):
        if self.phase == "list":
            if self.list_until is None:
                return
            self.phase = "play"
            return
        for name, rect in self.shelf_rects():
            if name not in self.packed and rect.contains(pt):
                if name in self.needed:
                    self.packed.append(name)
                    self.ctx.audio.sfx("pop")
                    if all(n in self.packed for n in self.needed):
                        self.finish(True)
                else:
                    self.err_impulsive += 1
                    self.shake = (name, time.monotonic() + 0.5)
                    self.ctx.audio.sfx("soft")
                    if self.err_impulsive >= 5:
                        self.finish(False)
                return
