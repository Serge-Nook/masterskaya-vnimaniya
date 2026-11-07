"""Мастерская 1 — «Внимание»."""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from mv import art, theme
from mv.exercises.base import H, W, Exercise
from mv.i18n import N_, tr
from mv.scenes import Scene, make_change, make_scene


class RedCircles(Exercise):
    key = "red_circles"
    workshop = "attention"
    title = N_("Найди красные кружочки")
    picture = "circle"
    intro = ["intro_red"]

    def setup(self):
        pw = self.power
        n_targets = 3 + min(4, (pw - 1) // 2)
        n_distract = 3 + pw * 2
        self.speed = 28 + pw * 11
        self.items = []
        kinds = []
        kinds += [("circle", theme.RED, True)] * n_targets
        for i in range(n_distract):
            if pw >= 4 and i % 3 == 0:
                kinds.append(("square", theme.RED, False))
            elif pw >= 7 and i % 3 == 1:
                kinds.append(("circle", theme.ORANGE, False))
            else:
                color = self.rng.choice([theme.BLUE, theme.GREEN, theme.YELLOW, theme.PURPLE])
                kinds.append((self.rng.choice(["circle", "square", "triangle"]), color, False))
        for shape, color, target in kinds:
            r = 46 if pw < 6 else 40
            self.items.append({
                "shape": shape, "color": QColor(color), "target": target, "r": r,
                "x": self.rng.uniform(80, W - 80), "y": self.rng.uniform(80, H - 80),
                "a": self.rng.uniform(0, 2 * math.pi), "found": False, "wobble": 0.0, "pop": 0.0,
            })
        self.remaining = n_targets
        self.hint_until = time.monotonic() + (3.0 if self.hint else 0)

    def tick(self, dt):
        for it in self.items:
            if it["found"]:
                it["pop"] = min(1.0, it["pop"] + dt * 2.5)
                continue
            it["a"] += self.rng.uniform(-0.4, 0.4) * dt
            it["x"] += math.cos(it["a"]) * self.speed * dt
            it["y"] += math.sin(it["a"]) * self.speed * dt
            r = it["r"]
            if it["x"] < r or it["x"] > W - r:
                it["a"] = math.pi - it["a"]
                it["x"] = max(r, min(W - r, it["x"]))
            if it["y"] < r or it["y"] > H - r:
                it["a"] = -it["a"]
                it["y"] = max(r, min(H - r, it["y"]))
            it["wobble"] = max(0.0, it["wobble"] - dt * 2)

    def paint(self, p: QPainter):
        self.panel(p, QRectF(0, 0, W, H), theme.BG_DEEP, 0)
        hint = time.monotonic() < self.hint_until
        for it in self.items:
            r = it["r"]
            if it["found"]:
                k = it["pop"]
                p.setOpacity(1 - k)
                art.draw(p, "star", QRectF(it["x"] - r, it["y"] - r - 30 * k, 2 * r, 2 * r))
                p.setOpacity(1)
                continue
            dx = math.sin(it["wobble"] * 20) * 8 * it["wobble"]
            rect = QRectF(it["x"] - r + dx, it["y"] - r, 2 * r, 2 * r)
            if hint and it["target"]:
                p.setPen(QPen(theme.FOCUS, 6))
                p.setBrush(Qt.BrushStyle.NoBrush)
                pulse = 8 + 6 * math.sin(time.monotonic() * 5)
                p.drawEllipse(rect.adjusted(-pulse, -pulse, pulse, pulse))
            art.draw(p, it["shape"], rect, it["color"])

    def press(self, pt):
        best = None
        for it in self.items:
            if it["found"]:
                continue
            d = math.hypot(pt.x() - it["x"], pt.y() - it["y"])
            if d <= it["r"] + 18 and (best is None or d < best[0]):
                best = (d, it)
        if best is None:
            return
        it = best[1]
        if it["target"]:
            it["found"] = True
            self.remaining -= 1
            self.ctx.audio.sfx("pop")
            if self.remaining == 0:
                self.finish(True)
        else:
            it["wobble"] = 1.0
            self.err_impulsive += 1
            self.ctx.audio.sfx("soft")
            if self.err_impulsive >= 6:
                self.finish(False)


class WhatChanged(Exercise):
    key = "what_changed"
    workshop = "attention"
    title = N_("Что изменилось?")
    picture = "house"
    intro = ["intro_changed"]

    SHOW_S = 2.0

    def setup(self):
        pw = self.power
        n_objects = min(10, 3 + (pw + 1) // 2)
        seed = self.rng.randrange(60)
        self.scene: Scene = make_scene(seed, n_objects, self.rng)
        self.changed, self.change = make_change(self.scene, self.rng, allow_move=pw >= 6)
        self.phase = "show"
        self.t = 0.0
        self.show_s = self.SHOW_S + (1.5 if self.hint else 0.0) + (1.0 if pw <= 2 else 0.0)
        self.tries = 0
        self.flash = None
        self.ctx.audio.say("remember")

    def tick(self, dt):
        self.t += dt
        if self.phase == "show" and self.t >= self.show_s:
            self.phase, self.t = "blank", 0.0
            self.ctx.audio.sfx("whoosh")
        elif self.phase == "blank" and self.t >= 0.6:
            self.phase, self.t = "ask", 0.0
            self.asked_at = time.monotonic()
            self.ctx.audio.say("what_changed")
        elif self.phase == "reveal" and self.t >= 1.6:
            self.phase = "over"
            self.finish(self.tries <= 2)

    def paint(self, p):
        if self.phase == "blank":
            self.panel(p, QRectF(0, 0, W, H), theme.PANEL, 0)
            return
        scene = self.scene if self.phase == "show" else self.changed
        scene.paint(p, QRectF(0, 0, W, H))
        if self.phase in ("reveal", "over") or (self.hint and self.phase == "ask" and self.t > 6):
            rect = self.change.rect
            p.setPen(QPen(theme.FOCUS, 7))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(rect.adjusted(-14, -14, 14, 14))
        if self.flash:
            pt, until = self.flash
            if time.monotonic() < until:
                p.setPen(QPen(theme.INK_SOFT, 4, Qt.PenStyle.DashLine))
                p.drawEllipse(pt, 30, 30)

    def press(self, pt):
        if self.phase != "ask":
            if self.phase in ("show", "blank"):
                return
            return
        if self.change.rect.adjusted(-30, -30, 30, 30).contains(pt):
            self.ctx.audio.sfx("pop")
            self.reactions.append((time.monotonic() - self.asked_at) * 1000)
            self.phase, self.t = "reveal", 0.0
        else:
            self.tries += 1
            if time.monotonic() - self.asked_at < 0.8:
                self.err_impulsive += 1
            else:
                self.err_omission += 1
            self.ctx.audio.sfx("soft")
            self.flash = (pt, time.monotonic() + 0.6)
            if self.tries >= 3:
                self.phase, self.t = "reveal", 0.0


LISTEN_SLOTS = 8


class ListenAndDo(Exercise):
    key = "listen_do"
    workshop = "attention"
    title = N_("Слушай и делай")
    picture = "bell"
    intro = ["intro_listen"]

    def setup(self):
        pw = self.power
        self.steps = 2 if pw <= 4 else 3
        n = min(len(art.LISTEN_OBJECTS), 4 + pw // 2 + (1 if self.steps == 3 else 0))
        self.objects = self.rng.sample(art.LISTEN_OBJECTS, n)
        cols = min(5, max(3, (n + 1) // 2))
        rows = math.ceil(n / cols)
        self.cells = []
        cw, ch = W / cols, (H - 40) / rows
        for i, name in enumerate(self.objects):
            c, r = i % cols, i // cols
            self.cells.append((name, QRectF(c * cw + 20, 20 + r * ch + 10, cw - 40, ch - 20)))
        self.sequence = self.rng.sample(self.objects, self.steps)
        self.pos = 0
        self.done_marks: list[str] = []
        self.wrong: tuple[str, float] | None = None
        self.listening = True
        self.instruction_count = 0
        self._speak()

    def _speak(self):
        keys = ["listen_first", f"acc_{self.sequence[0]}", "listen_then", f"acc_{self.sequence[1]}"]
        if self.steps == 3:
            keys += ["listen_last", f"acc_{self.sequence[2]}"]
        self.listening = True
        self.instruction_count += 1
        self.ctx.audio.say(keys)
        self.listen_audio(self._spoken)

    def _spoken(self):
        self.unlisten_audio()
        self.listening = False
        self.ready_at = time.monotonic()

    def stop(self):
        super().stop()
        self.unlisten_audio()

    def actions(self):
        return [(tr("Послушать ещё раз"), self._speak)]

    def paint(self, p):
        now = time.monotonic()
        for name, rect in self.cells:
            done = name in self.done_marks
            self.panel(p, rect, theme.ACCENT_LIGHT if done else theme.PANEL)
            if self.hint and not self.listening and self.pos < self.steps and name == self.sequence[self.pos]:
                p.setPen(QPen(theme.FOCUS, 6))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(rect, 26, 26)
            shake = 0.0
            if self.wrong and self.wrong[0] == name and now < self.wrong[1]:
                shake = math.sin(now * 40) * 8
            art.draw(p, name, rect.adjusted(20 + shake, 16, -20 + shake, -16), opacity=0.55 if done else 1)
            if done:
                idx = self.done_marks.index(name) + 1
                self.text(p, QRectF(rect.left() + 10, rect.top() + 6, 50, 50), str(idx), 36, theme.ACCENT)

    def press(self, pt):
        for name, rect in self.cells:
            if rect.contains(pt):
                break
        else:
            return
        if name in self.done_marks:
            return
        if self.listening:
            self.err_impulsive += 1
            self.wrong = (name, time.monotonic() + 0.5)
            self.ctx.audio.sfx("soft")
            return
        if name == self.sequence[self.pos]:
            if self.pos == 0:
                self.reactions.append((time.monotonic() - self.ready_at) * 1000)
            self.done_marks.append(name)
            self.pos += 1
            self.ctx.audio.sfx("pop")
            if self.pos == self.steps:
                self.finish(True, 3 if self.err_sequence + self.err_impulsive == 0 and self.instruction_count == 1 else 2 if self.err_sequence <= 1 else 1)
        else:
            self.err_sequence += 1
            self.wrong = (name, time.monotonic() + 0.5)
            self.ctx.audio.sfx("soft")
            if self.err_sequence >= 3:
                self.finish(False)


class StopGame(Exercise):
    key = "stop_game"
    workshop = "attention"
    title = N_("Стоп-игра")
    picture = "balloon"
    intro = ["intro_stop"]

    @classmethod
    def intro_keys(cls, level):
        return ["intro_stop", "intro_stop_nogo"] if level >= 4 else ["intro_stop"]

    def setup(self):
        pw = self.power
        self.trials = 5
        self.trial = 0
        self.correct = 0
        self.nogo_enabled = self.level >= 4 or pw >= 6
        self.speed = 50 + pw * 9
        self.balloons = []
        colors = [theme.RED, theme.BLUE, theme.YELLOW, theme.GREEN, theme.PURPLE, theme.ORANGE]
        for i in range(5 + pw // 2):
            self.balloons.append({"x": self.rng.uniform(60, W - 60), "y": self.rng.uniform(H * 0.3, H + 100),
                                  "c": colors[i % len(colors)], "ph": self.rng.uniform(0, 6)})
        self.state = "moving"
        self.frozen_until = 0.0
        self.message = ""
        self._schedule()

    def _schedule(self):
        self.signal_at = time.monotonic() + self.rng.uniform(2.0, 4.5)
        self.signal_kind = "pipe" if self.nogo_enabled and self.rng.random() < 0.3 else "bell"
        self.signaled = False

    def actions(self):
        return [(tr("СТОП"), self.stop_pressed)]

    def tick(self, dt):
        now = time.monotonic()
        if self.state == "frozen":
            if now >= self.frozen_until:
                self.state = "moving"
                self.message = ""
                if self.trial >= self.trials:
                    self.finish(self.correct >= self.trials - 1,
                                3 if self.correct == self.trials and self.err_impulsive == 0 else 2 if self.correct >= self.trials - 1 else 1)
                    return
                self._schedule()
            return
        for b in self.balloons:
            b["y"] -= self.speed * dt
            b["ph"] += dt
            if b["y"] < -120:
                b["y"] = H + 80
                b["x"] = self.rng.uniform(60, W - 60)
        if not self.signaled and now >= self.signal_at:
            self.signaled = True
            self.ctx.audio.sfx(self.signal_kind)
        if self.signaled:
            limit = 2.2 if self.signal_kind == "bell" else 1.8
            if now - self.signal_at > limit:
                if self.signal_kind == "bell":
                    self.err_omission += 1
                    self.message = tr("Колокольчик уже звенел!")
                else:
                    self.correct += 1
                    self.message = tr("Правильно, дудочку пропускаем!")
                self._end_trial()

    def _end_trial(self):
        self.trial += 1
        self.state = "frozen"
        self.frozen_until = time.monotonic() + 1.4

    def stop_pressed(self):
        if self.finished or self.state == "frozen":
            return
        now = time.monotonic()
        if not self.signaled:
            self.err_impulsive += 1
            self.ctx.audio.say("stop_wait")
            self.message = tr("Подожди колокольчик")
            self.signal_at = max(self.signal_at, now + 1.5)
            return
        if self.signal_kind == "bell":
            self.reactions.append((now - self.signal_at) * 1000)
            self.correct += 1
            self.ctx.audio.sfx("pop")
            self.message = tr("Стоп! Молодец!")
        else:
            self.err_impulsive += 1
            self.message = tr("Это была дудочка")
            self.ctx.audio.sfx("soft")
        self._end_trial()

    def press(self, pt):
        self.stop_pressed()

    def on_key(self, key):
        if key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.stop_pressed()
            return True
        return False

    def paint(self, p):
        self.panel(p, QRectF(0, 0, W, H), theme.SKY, 0)
        for b in self.balloons:
            x = b["x"] + math.sin(b["ph"] * 1.2) * 14
            art.draw(p, "balloon", QRectF(x - 50, b["y"] - 60, 100, 120), b["c"])
        for i in range(self.trials):
            done = i < self.trial
            art.draw(p, "bell", QRectF(20 + i * 52, 16, 44, 44), theme.STAR if done else QColor("#DDE5E1"))
        if self.message:
            self.panel(p, QRectF(W / 2 - 330, H - 120, 660, 90))
            self.text(p, QRectF(W / 2 - 330, H - 120, 660, 90), self.message, 38)
        if self.hint and self.signaled and self.state == "moving" and self.signal_kind == "bell":
            art.draw(p, "bell", QRectF(W / 2 - 80, H / 2 - 80, 160, 160))
