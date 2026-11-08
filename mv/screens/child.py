"""Экраны режима ребёнка."""
from __future__ import annotations

import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from mv import APP_NAME, art, theme
from mv.exercises.registry import WORKSHOPS, workshop
from mv.i18n import tr
from mv.phrases import PRAISE, RETRY, WARMUPS
from mv.widgets import Hourglass, PictureButton, Screen, StarCounter, StarsRow, TikhonPanel, make_button


class DisclaimerScreen(Screen):
    def __init__(self, ctx):
        super().__init__(ctx)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(80, 60, 80, 60)
        title = QLabel(tr(APP_NAME))
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text = QLabel(
            "<p style='font-size:30px; font-weight:800'>" + tr("Приложение не заменяет консультацию специалиста.") + "</p>"
            "<p>" + tr("«Мастерская внимания» — вспомогательный тренажёр для детей 6–7 лет. Короткие занятия"
                       " (5–10 минут) помогают тренировать внимание, сдержанность, слуховую последовательность и"
                       " саморегуляцию. Занятия проводятся по согласованию с врачом или психологом.") + "</p>"
            "<p>" + tr("Приложение работает без интернета и хранит все данные только на этом компьютере.") + "</p>"
            "<p>" + tr("Настройки и статистика — в режиме взрослого (кнопка «Взрослым» на главном экране).") + "</p>"
        )
        text.setWordWrap(True)
        text.setStyleSheet("QLabel { background: #FBFAF5; border-radius: 24px; padding: 30px; font-size: 24px; }")
        ok = make_button(tr("Понятно"), primary=True, slot=self._accept)
        lay.addWidget(title)
        lay.addSpacing(20)
        lay.addWidget(text, 1)
        lay.addSpacing(20)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(ok)
        row.addStretch(1)
        lay.addLayout(row)

    def _accept(self):
        self.ctx.db.set("disclaimer_accepted", True)
        self.ctx.window.go_home(greet=True)


class HomeScreen(Screen):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.panel = TikhonPanel(ctx, next_text=tr("Слушаю"))
        self.panel.next.hide()
        self.stars = StarCounter()
        cards = QHBoxLayout()
        cards.setSpacing(24)
        self.cards = []
        for ws in WORKSHOPS:
            b = PictureButton(tr(ws["title"]), ws["picture"])
            b.clicked.connect(lambda _=False, k=ws["key"]: ctx.window.open_workshop(k))
            cards.addWidget(b)
            self.cards.append(b)
        reward = "garden" if ctx.db.get("reward") == "garden" else "aquarium"
        self.garden = PictureButton(tr("Мой сад") if reward == "garden" else tr("Мой аквариум"),
                                    "flower" if reward == "garden" else "fish", big=False)
        self.garden.clicked.connect(ctx.window.open_garden)
        self.adult = make_button(tr("Взрослым"), slot=ctx.window.open_adult)
        self.quit = make_button(tr("Выход"), slot=ctx.window.quit_app)
        top = QHBoxLayout()
        top.addWidget(self.stars)
        top.addStretch(1)
        top.addWidget(self.adult)
        top.addWidget(self.quit)
        bottom = QHBoxLayout()
        bottom.addLayout(cards, 5)
        bottom.addWidget(self.garden, 1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 30)
        lay.addLayout(top)
        lay.addWidget(self.panel, 5)
        lay.addLayout(bottom, 5)

    def on_enter(self):
        self.stars.set_count(self.ctx.db.total_stars())
        greet = getattr(self, "greet_key", "hello_again")
        state = "bye" if greet in ("bye",) else "greet"
        self.panel.say(greet, state)
        self.greet_key = "hello_again"

    def first_focus(self):
        return self.cards[0]


class WorkshopScreen(Screen):
    def __init__(self, ctx, key: str):
        super().__init__(ctx)
        self.ws = workshop(key)
        self.panel = TikhonPanel(ctx)
        self.panel.next.hide()
        title = QLabel(tr(self.ws["title"]))
        title.setObjectName("Title")
        back = make_button(tr("Назад"), slot=self.back)
        top = QHBoxLayout()
        top.addWidget(back)
        top.addSpacing(20)
        top.addWidget(title)
        top.addStretch(1)
        grid = QHBoxLayout()
        grid.setSpacing(24)
        self.buttons = []
        for cls in self.ws["exercises"]:
            b = PictureButton(tr(cls.title), cls.picture)
            b.badge = ""
            b.clicked.connect(lambda _=False, c=cls: ctx.window.start_exercise(c))
            grid.addWidget(b)
            self.buttons.append((cls, b))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 30)
        lay.addLayout(top)
        lay.addWidget(self.panel, 4)
        lay.addLayout(grid, 5)

    def on_enter(self):
        for cls, b in self.buttons:
            b.badge = tr("ур. %1").replace("%1", str(self.ctx.db.level_for(cls.key)))
        self.panel.say([self.ws["voice"], "choose_game"], "explain")

    def first_focus(self):
        return self.buttons[0][1]

    def back(self):
        self.ctx.window.go_home()


class ExerciseHost(Screen):
    """Цикл: Тихон объясняет → уровень → Тихон хвалит/подбадривает → следующий уровень."""

    def __init__(self, ctx, cls):
        super().__init__(ctx)
        self.cls = cls
        self.ex = None
        self.hint = False
        self.level = 1
        self.result = None

        self.hourglass = Hourglass()
        self.title = QLabel(tr(cls.title))
        self.title.setObjectName("Subtitle")
        self.back_btn = make_button(tr("Назад"), slot=self.back)
        top = QHBoxLayout()
        top.addWidget(self.back_btn)
        top.addSpacing(16)
        top.addWidget(self.title)
        top.addStretch(1)
        top.addWidget(self.hourglass)

        self.panel = TikhonPanel(ctx)
        self.panel.proceed.connect(self._proceed)
        self.stars = StarsRow()
        self.panel.extra.addWidget(self.stars)
        self.stars.hide()

        self.ex_box = QVBoxLayout()
        self.subtitle = QLabel("")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("QLabel { font-size: 26px; font-weight: 700; color: #23343B; }")
        self.subtitle.setFixedHeight(40)
        self.actions_row = QHBoxLayout()
        self.ex_area = QWidget()
        ex_lay = QVBoxLayout(self.ex_area)
        ex_lay.setContentsMargins(0, 0, 0, 0)
        ex_lay.addLayout(self.ex_box, 1)
        ex_lay.addWidget(self.subtitle)
        ex_lay.addLayout(self.actions_row)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 14, 24, 14)
        lay.addLayout(top)
        lay.addWidget(self.panel, 1)
        lay.addWidget(self.ex_area, 1)
        self.ex_area.hide()
        ctx.audio.subtitle.connect(self._subtitle)
        ctx.session.tick.connect(self.hourglass.set_fraction)
        self.mode = "intro"

    def _subtitle(self, text):
        if self.ex_area.isVisible():
            self.subtitle.setText(text)

    def on_enter(self):
        self.hourglass.set_fraction(self.ctx.session.remaining_fraction())
        self.show_intro()

    def on_leave(self):
        self._drop_exercise()

    def show_intro(self):
        self.mode = "intro"
        self.level = self.ctx.db.level_for(self.cls.key)
        self.ex_area.hide()
        self.panel.show()
        self.stars.hide()
        self.panel.next.setText(tr("Начать"))
        keys = self.cls.intro_keys(self.level)
        self.panel.say(keys, "explain")
        self.panel.next.setFocus()

    def _proceed(self):
        self.ctx.audio.stop_voice()
        if self.mode in ("intro", "feedback"):
            if self.ctx.session.expired:
                self.ctx.window.start_break()
                return
            self.run_level()

    def _drop_exercise(self):
        if self.ex is not None:
            self.ex.stop()
            self.ex.done.disconnect()
            self.ex.setParent(None)
            self.ex.deleteLater()
            self.ex = None
        while self.actions_row.count():
            item = self.actions_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def run_level(self):
        self._drop_exercise()
        self.mode = "play"
        self.ctx.session.ensure_started()
        diff = int(self.ctx.db.get(f"difficulty_{self.cls.workshop}") or 2)
        self.ex = self.cls(self.ctx)
        self.ex.done.connect(self._level_done)
        self.ex_box.addWidget(self.ex)
        self.actions_row.addStretch(1)
        for text, slot in self.ex.actions():
            b = make_button(text, primary=True, slot=slot)
            b.setMinimumWidth(220)
            self.actions_row.addWidget(b)
        self.actions_row.addStretch(1)
        self.subtitle.setText("")
        self.panel.hide()
        self.ex_area.show()
        self.ex.start(self.level, diff, self.hint)
        self.ex.setFocus()
        self.title.setText(tr(self.cls.title) + "  ·  " + tr("уровень %1").replace("%1", str(self.level)))

    def _level_done(self, result):
        self.ctx.db.record_attempt(self.ctx.session.id, self.cls.workshop, self.cls.key, self.level, result)
        self._drop_exercise()
        self.mode = "feedback"
        self.ex_area.hide()
        self.panel.show()
        self.title.setText(tr(self.cls.title))
        if result.success:
            self.hint = False
            self.stars.show()
            self.stars.show_stars(result.stars)
            self.ctx.audio.sfx("chime")
            key = random.choice(PRAISE)
            self.panel.say(key, random.choice(["praise", "joy"]))
        else:
            self.hint = True
            self.stars.hide()
            self.panel.say(random.choice(RETRY), "retry")
        self.level = self.ctx.db.level_for(self.cls.key)
        if self.ctx.session.expired:
            self.panel.next.setText(tr("Перерыв"))
        else:
            self.panel.next.setText(tr("Ещё"))
        self.panel.next.setFocus()

    def abort(self):
        self._drop_exercise()
        self.mode = "intro"
        self.ex_area.hide()
        self.panel.show()
        self.panel.say("error_module", "think")

    def back(self):
        self.ctx.audio.stop_voice()
        self.ctx.window.open_workshop(self.cls.workshop)


class BreakScreen(Screen):
    """Обязательная перемена активности. Ребёнок не может её пропустить."""

    def __init__(self, ctx):
        super().__init__(ctx)
        from mv.figures import draw_pose

        self.draw_pose = draw_pose
        self.panel = TikhonPanel(ctx, next_text=tr("Готово"))
        self.panel.proceed.connect(self._next)
        self.panel.repeat.clicked.disconnect()
        self.panel.repeat.clicked.connect(lambda: self.panel.replay())
        self.figure = _PoseView()
        self.figure.setMinimumHeight(260)
        self.panel.extra.addWidget(self.figure)
        self.wait_label = QLabel("")
        self.wait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wait_label.setObjectName("Subtitle")
        self.hourglass = Hourglass()
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.hourglass)
        row.addWidget(self.wait_label)
        row.addStretch(1)
        self.adult = make_button(tr("Взрослым"), slot=ctx.window.open_adult)
        top = QHBoxLayout()
        top.addStretch(1)
        top.addWidget(self.adult)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 30)
        lay.addLayout(top)
        lay.addWidget(self.panel, 1)
        lay.addLayout(row)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.cards: list[str] = []
        self.index = -1
        self.total = 1.0

    def on_enter(self):
        remaining = self.ctx.db.pending_break()
        self.total = max(1.0, float(self.ctx.db.get("break_minutes")) * 60)
        self.cards = random.sample(WARMUPS, 3)
        self.index = -1
        self.figure.pose = None
        key = "time_up" if remaining > self.total - 5 else "break_intro"
        self.panel.say([key, "break_intro"] if key == "time_up" else [key], "explain")
        self.panel.next.setText(tr("Начать"))
        self.panel.next.setEnabled(True)
        self.timer.start(250)
        self._tick()

    def on_leave(self):
        self.timer.stop()

    def _next(self):
        self.index += 1
        if self.index < len(self.cards):
            card = self.cards[self.index]
            self.figure.pose = card
            self.panel.say(card, "explain")
            self.panel.next.setText(tr("Готово"))
            return
        self.figure.pose = None
        if self.ctx.db.pending_break() > 0:
            self.panel.say("break_intro", "breathe")
            self.panel.next.setEnabled(False)
        else:
            self._finish()

    def _tick(self):
        left = self.ctx.db.pending_break()
        self.hourglass.set_fraction(left / self.total)
        m, s = divmod(int(math.ceil(left)), 60)
        self.wait_label.setText(tr("Перерыв: %1").replace("%1", f"{m}:{s:02d}") if left > 0 else tr("Перерыв окончен"))
        if left <= 0 and self.index >= len(self.cards):
            self._finish()

    def _finish(self):
        self.timer.stop()
        self.ctx.db.finish_break()
        self.ctx.window.after_break()

    def back(self):
        pass


class _PoseView(QWidget):
    def __init__(self):
        super().__init__()
        self.pose = None
        self.t0 = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(33)

    def paintEvent(self, _):
        if not self.pose:
            return
        from mv.figures import draw_pose

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw_pose(p, self.pose, QRectF(0, 0, self.width(), self.height()), time.monotonic() - self.t0)
        p.end()


class DayDoneScreen(Screen):
    """Дневной лимит исчерпан — снимается только взрослым."""

    def __init__(self, ctx):
        super().__init__(ctx)
        self.panel = TikhonPanel(ctx)
        self.panel.next.hide()
        adult = make_button(tr("Взрослым"), slot=ctx.window.open_adult)
        quit_btn = make_button(tr("Выход"), slot=ctx.window.quit_app)
        top = QHBoxLayout()
        top.addStretch(1)
        top.addWidget(adult)
        top.addWidget(quit_btn)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 30)
        lay.addLayout(top)
        lay.addWidget(self.panel, 1)

    def on_enter(self):
        self.panel.say("day_done", "bye")

    def back(self):
        pass


class GardenScreen(Screen):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.view = GardenView(ctx)
        self.label = QLabel("")
        self.label.setObjectName("Subtitle")
        self.label.setWordWrap(True)
        back = make_button(tr("Назад"), slot=self.back)
        top = QHBoxLayout()
        top.addWidget(back)
        top.addSpacing(16)
        top.addWidget(self.label, 1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 14, 24, 24)
        lay.addLayout(top)
        lay.addWidget(self.view, 1)
        ctx.audio.subtitle.connect(self._subtitle)

    def _subtitle(self, text):
        if self.isVisible():
            self.label.setText(text)

    def on_enter(self):
        self.view.stars = self.ctx.db.total_stars()
        self.view.kind = self.ctx.db.get("reward")
        self.ctx.audio.say("garden_intro" if self.view.kind == "garden" else "aquarium_intro")

    def back(self):
        self.ctx.audio.stop_voice()
        self.ctx.window.go_home()


class GardenView(QWidget):
    PLANTS = ["flower", "tree", "flower", "apple", "flower", "hedgehog", "flower", "tree"]

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.stars = 0
        self.kind = "garden"
        self.t0 = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(33)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        t = time.monotonic() - self.t0
        rng = random.Random(42)
        if self.kind == "aquarium":
            p.fillRect(self.rect(), QColor("#BFE0EC"))
            p.fillRect(QRectF(0, h * 0.86, w, h * 0.14), QColor("#EAD8AE"))
            fish = min(40, self.stars // 2)
            colors = [theme.ORANGE, theme.YELLOW, theme.PINK, theme.BLUE, theme.PURPLE, theme.RED]
            for i in range(fish):
                y = h * 0.12 + rng.random() * h * 0.66
                speed = 20 + rng.random() * 25
                x = (rng.random() * w + t * speed) % (w + 120) - 60
                art.draw(p, "fish", QRectF(x - 40, y - 30, 80, 60), colors[i % len(colors)])
            for i in range(6):
                x = w * (0.1 + i * 0.16)
                p.setPen(QPen(theme.GREEN, 8))
                for k in range(4):
                    sway = math.sin(t * 0.8 + i + k) * 6
                    p.drawLine(QPointF(x + sway * k / 3, h * 0.86 - k * 30), QPointF(x + sway * (k + 1) / 3, h * 0.86 - (k + 1) * 30))
        else:
            p.fillRect(QRectF(0, 0, w, h * 0.55), QColor("#D6ECF5"))
            p.fillRect(QRectF(0, h * 0.55, w, h * 0.45), QColor("#B9D9A6"))
            art.draw(p, "sun", QRectF(w - 150, 20, 120, 120))
            cols, rows = 10, 3
            plants = min(cols * rows, (self.stars + 2) // 3)
            for i in sorted(range(plants), key=lambda k: k % rows):
                r, c = i % rows, (i // rows * 7) % cols
                x = (c + 0.5 + (0.5 if r % 2 else 0)) * w / (cols + 0.5) + rng.uniform(-10, 10)
                y = h * 0.66 + r * 0.13 * h
                size = min(w / cols * 0.85, h * 0.15) * (0.96 + 0.04 * math.sin(t * 0.7 + i))
                name = self.PLANTS[i % len(self.PLANTS)]
                colors = [theme.PINK, theme.YELLOW, theme.PURPLE, theme.RED, theme.BLUE]
                art.draw(p, name, QRectF(x - size / 2, y - size * 0.6, size, size), colors[i % 5] if name == "flower" else None)
        art.draw(p, "star", QRectF(20, 20, 60, 60))
        f = p.font()
        f.setPixelSize(40)
        f.setBold(True)
        p.setFont(f)
        p.setPen(theme.INK)
        p.drawText(QRectF(90, 20, 300, 60), Qt.AlignmentFlag.AlignVCenter, str(self.stars))
        p.end()
