from __future__ import annotations

import time

from PySide6.QtCore import QObject, QTimer, Signal


class Session(QObject):
    """Занятие: таймер «песочные часы», учёт активного времени, автосохранение."""

    tick = Signal(float)
    time_up = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.id: int | None = None
        self.planned_s = 0
        self.active_s = 0.0
        self.paused = False
        self.expired = False
        self._last = time.monotonic()
        self._saved_at = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    @property
    def running(self) -> bool:
        return self.id is not None

    def remaining_fraction(self) -> float:
        if not self.running or self.planned_s <= 0:
            return 1.0
        return max(0.0, 1.0 - self.active_s / self.planned_s)

    def daily_limit_reached(self) -> bool:
        import datetime as dt

        if self.db.get("limit_lifted_on") == dt.date.today().isoformat():
            return False
        limit = int(self.db.get("daily_limit_minutes") or 0)
        return limit > 0 and self.db.minutes_today() >= limit

    def ensure_started(self) -> None:
        if self.running:
            return
        self.planned_s = max(5, min(10, int(self.db.get("session_minutes")))) * 60
        self.id = self.db.start_session(self.planned_s)
        self.active_s = 0.0
        self.expired = False
        self.paused = False
        self._last = time.monotonic()
        self.timer.start(250)

    def pause(self, value: bool) -> None:
        self._accumulate()
        self.paused = value

    def _accumulate(self) -> None:
        now = time.monotonic()
        if self.running and not self.paused:
            self.active_s += now - self._last
        self._last = now

    def _tick(self) -> None:
        self._accumulate()
        if not self.running:
            return
        if time.monotonic() - self._saved_at > 10:
            self._saved_at = time.monotonic()
            self.db.update_session(self.id, self.active_s)
        self.tick.emit(self.remaining_fraction())
        if not self.expired and self.active_s >= self.planned_s:
            self.expired = True
            self.time_up.emit()

    def end(self) -> None:
        if not self.running:
            return
        self._accumulate()
        self.db.update_session(self.id, self.active_s, ended=True)
        self.id = None
        self.timer.stop()
