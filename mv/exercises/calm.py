"""Мастерская 3 — «Спокойствие»."""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from mv import theme
from mv.exercises.base import H, W, Exercise
from mv.i18n import N_, tr
from mv.phrases import WARMUPS
from mv.tikhon import draw_tikhon
from mv.figures import draw_pose


class Breathing(Exercise):
    key = "breathing"
    workshop = "calm"
    title = N_("Дыхание Тихона")
    picture = "balloon"
    intro = ["intro_breath"]

    BEAT = 1.0  # 60 ударов в минуту
    INHALE_BEATS = 4
    EXHALE_BEATS = 4

    def setup(self):
        self.cycles = int(self.ctx.db.get("breath_cycles") or 10)
        self.cycles = max(10, min(15, self.cycles))
        self.t = 0.0
        self.cycle = 0
        self.last_beat = -1
        self.last_phase = None
        self.anim_t0 = time.monotonic()

    @property
    def period(self):
        return self.BEAT * (self.INHALE_BEATS + self.EXHALE_BEATS)

    def actions(self):
        return [(tr("Хватит"), lambda: self.finish(True, 1 if self.cycle < 3 else 2))]

    def breath_value(self) -> tuple[float, str]:
        k = self.t % self.period
        inhale = self.BEAT * self.INHALE_BEATS
        if k < inhale:
            x = k / inhale
            return 0.5 - 0.5 * math.cos(math.pi * x), "inhale"
        x = (k - inhale) / (self.period - inhale)
        return 0.5 + 0.5 * math.cos(math.pi * x), "exhale"

    def tick(self, dt):
        self.t += dt
        self.cycle = int(self.t // self.period)
        beat = int(self.t // self.BEAT)
        if beat != self.last_beat:
            self.last_beat = beat
            self.ctx.audio.sfx("tick")
        _, phase = self.breath_value()
        if phase != self.last_phase:
            self.last_phase = phase
            if self.cycle < 3:
                self.ctx.audio.say(phase)
        if self.cycle >= self.cycles:
            self.finish(True, 3)

    def paint(self, p):
        self.panel(p, QRectF(0, 0, W, H), QColor("#E3EEF3"), 0)
        v, phase = self.breath_value()
        r = 110 + 150 * v
        c = QPointF(W * 0.66, H * 0.5)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(110, 170, 200, 60))
        p.drawEllipse(c, r + 30, r + 30)
        p.setBrush(QColor(110, 170, 200, 140))
        p.drawEllipse(c, r, r)
        self.text(p, QRectF(c.x() - 200, c.y() - 40, 400, 80), tr("Вдох…") if phase == "inhale" else tr("Выдох…"), 54, "white")
        p.save()
        p.translate(W * 0.08, 70)
        p.scale(2.1, 2.1)
        draw_tikhon(p, "breathe", time.monotonic() - self.anim_t0, 0, False, v)
        p.restore()
        done = min(self.cycle, self.cycles)
        for i in range(self.cycles):
            p.setBrush(theme.ACCENT if i < done else QColor("#C9D8D2"))
            p.drawEllipse(QPointF(W / 2 - self.cycles * 14 + i * 28 + 14, H - 30), 9, 9)


class Rainbow(Exercise):
    key = "rainbow"
    workshop = "calm"
    title = N_("Медленная радуга")
    picture = "rainbow"
    intro = ["intro_rainbow"]

    SAMPLES = 90

    def setup(self):
        self.center = QPointF(W / 2, H - 40)
        n = 5 if self.power <= 4 else 7
        self.colors = theme.RAINBOW[:n] if n == 7 else [theme.RAINBOW[i] for i in (0, 2, 3, 5, 6)]
        self.band = 46 if n == 5 else 36
        self.r0 = 520
        self.filled = [[0.0] * self.SAMPLES for _ in self.colors]
        self.last: tuple[QPointF, float] | None = None
        self.too_fast_until = 0.0
        self.fast_count = 0
        self.speed_limit = 1100 - min(500, self.power * 40)
        self.ctx.audio.play_music("calm")

    def stop(self):
        super().stop()
        self.ctx.audio.stop_music()

    def actions(self):
        return [(tr("Готово"), self._done)]

    def _done(self):
        self.finish(True, self._stars())

    def _stars(self):
        k = self.progress()
        return 3 if k > 0.9 else 2 if k > 0.6 else 1

    def progress(self) -> float:
        total = sum(sum(row) for row in self.filled)
        return total / (len(self.filled) * self.SAMPLES)

    def _paint_at(self, pt: QPointF) -> None:
        dx, dy = pt.x() - self.center.x(), self.center.y() - pt.y()
        if dy < -10:
            return
        d = math.hypot(dx, dy)
        ang = math.atan2(dy, dx)
        if not (0 <= ang <= math.pi):
            return
        idx = int((self.r0 - d) // self.band)
        if 0 <= idx < len(self.colors):
            s = int((math.pi - ang) / math.pi * (self.SAMPLES - 1))
            for k in range(s - 2, s + 3):
                if 0 <= k < self.SAMPLES:
                    self.filled[idx][k] = min(1.0, self.filled[idx][k] + 0.5)

    def press(self, pt):
        self.last = (pt, time.monotonic())
        self._paint_at(pt)

    def move(self, pt, pressed):
        if not pressed or self.last is None:
            return
        prev, t0 = self.last
        now = time.monotonic()
        dt = max(1e-3, now - t0)
        dist = math.hypot(pt.x() - prev.x(), pt.y() - prev.y())
        if dt < 0.012 and dist < 6:
            return
        speed = dist / dt
        self.last = (pt, now)
        if speed > self.speed_limit:
            if now > self.too_fast_until:
                self.fast_count += 1
                if self.fast_count % 3 == 1:
                    self.ctx.audio.say("slower")
            self.too_fast_until = now + 1.2
            return
        steps = max(1, int(dist / 6))
        for i in range(1, steps + 1):
            self._paint_at(QPointF(prev.x() + (pt.x() - prev.x()) * i / steps, prev.y() + (pt.y() - prev.y()) * i / steps))
        if self.progress() > 0.96:
            self.finish(True, 3)

    def release(self, pt):
        self.last = None

    def paint(self, p):
        self.panel(p, QRectF(0, 0, W, H), QColor("#EEF5F8"), 0)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("white"))
        for cx, cy, s in ((160, 520, 1.0), (1120, 540, 1.2)):
            for dx, dy, r in ((-50, 0, 46), (0, -26, 58), (52, 0, 46)):
                p.drawEllipse(QPointF(cx + dx * s, cy + dy * s), r * s, r * s)
        for i, color in enumerate(self.colors):
            r_out = self.r0 - i * self.band
            r_mid = r_out - self.band / 2
            outline = QPen(QColor("#C6D3D8"), 2, Qt.PenStyle.DashLine)
            p.setPen(outline)
            p.setBrush(Qt.BrushStyle.NoBrush)
            rect = QRectF(self.center.x() - r_out, self.center.y() - r_out, 2 * r_out, 2 * r_out)
            p.drawArc(rect, 0, 180 * 16)
            pen = QPen(color, self.band - 4)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen)
            seg = 180.0 / self.SAMPLES
            mid_rect = QRectF(self.center.x() - r_mid, self.center.y() - r_mid, 2 * r_mid, 2 * r_mid)
            for k, val in enumerate(self.filled[i]):
                if val > 0:
                    p.setOpacity(min(1.0, val))
                    start = 180 - (k + 1) * seg
                    p.drawArc(mid_rect, int(start * 16), int((seg + 0.6) * 16))
            p.setOpacity(1)
        inner = self.r0 - len(self.colors) * self.band
        p.setPen(QPen(QColor("#C6D3D8"), 2, Qt.PenStyle.DashLine))
        p.drawArc(QRectF(self.center.x() - inner, self.center.y() - inner, 2 * inner, 2 * inner), 0, 180 * 16)
        if time.monotonic() < self.too_fast_until:
            self.panel(p, QRectF(W / 2 - 220, 20, 440, 70))
            self.text(p, QRectF(W / 2 - 220, 20, 440, 70), tr("Медленнее…"), 36)


class Warmup(Exercise):
    key = "warmup"
    workshop = "calm"
    title = N_("Разминка")
    picture = "sun"
    intro = ["intro_warmup"]

    def setup(self):
        self.cards = self.rng.sample(WARMUPS, 3)
        self.index = 0
        self.anim_t0 = time.monotonic()
        self._speak()

    def _speak(self):
        self.ctx.audio.say(self.cards[self.index])

    def actions(self):
        return [(tr("Повторить"), self._speak), (tr("Готово"), self.next_card)]

    def next_card(self):
        if self.finished:
            return
        self.ctx.audio.sfx("chime")
        self.index += 1
        if self.index >= len(self.cards):
            self.finish(True, 3)
            return
        self._speak()

    def on_key(self, key):
        if key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.next_card()
            return True
        return False

    def paint(self, p):
        from mv.audio import phrase_text

        self.panel(p, QRectF(0, 0, W, H), QColor("#F5EEDD"), 0)
        if self.index >= len(self.cards):
            return
        card = self.cards[self.index]
        self.panel(p, QRectF(80, 40, W - 160, H - 80))
        draw_pose(p, card, QRectF(120, 70, 480, 500), time.monotonic() - self.anim_t0)
        self.text(p, QRectF(640, 120, 560, 360), phrase_text([card]), 46)
        for i in range(len(self.cards)):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(theme.ACCENT if i <= self.index else QColor("#D8D0BC"))
            p.drawEllipse(QPointF(W / 2 - 40 + i * 40, H - 64), 10, 10)


ALL_CALM = [Breathing, Rainbow, Warmup]
