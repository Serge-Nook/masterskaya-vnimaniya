from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path

MIGRATIONS: list[str] = [
    # 1
    """
    CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started REAL NOT NULL,
        ended REAL,
        planned_s INTEGER NOT NULL,
        active_s REAL NOT NULL DEFAULT 0
    );
    CREATE TABLE attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
        ts REAL NOT NULL,
        workshop TEXT NOT NULL,
        exercise TEXT NOT NULL,
        level INTEGER NOT NULL,
        success INTEGER NOT NULL,
        stars INTEGER NOT NULL,
        duration_ms INTEGER NOT NULL,
        err_impulsive INTEGER NOT NULL DEFAULT 0,
        err_sequence INTEGER NOT NULL DEFAULT 0,
        err_omission INTEGER NOT NULL DEFAULT 0,
        reaction_ms REAL
    );
    CREATE INDEX attempts_ts ON attempts(ts);
    CREATE TABLE progress (exercise TEXT PRIMARY KEY, level INTEGER NOT NULL, fails INTEGER NOT NULL DEFAULT 0);
    """,
    # 2
    """
    CREATE TABLE breaks (id INTEGER PRIMARY KEY AUTOINCREMENT, started REAL NOT NULL, until REAL NOT NULL, done INTEGER NOT NULL DEFAULT 0);
    """,
]

DEFAULTS: dict[str, object] = {
    "disclaimer_accepted": False,
    "language": "",
    "session_minutes": 7,
    "break_minutes": 2,
    "daily_limit_minutes": 30,
    "volume": 60,
    "volume_cap": 70,
    "voice": True,
    "music": True,
    "fullscreen": True,
    "reward": "garden",
    "breath_cycles": 10,
    "difficulty_attention": 2,
    "difficulty_planning": 2,
    "difficulty_calm": 2,
    "pin_hash": "",
    "pin_salt": "",
    "limit_lifted_on": "",
}

MAX_LEVEL = 10


@dataclass
class LevelResult:
    success: bool
    stars: int
    duration_ms: int
    err_impulsive: int = 0
    err_sequence: int = 0
    err_omission: int = 0
    reactions: list[float] = field(default_factory=list)

    @property
    def reaction_ms(self) -> float | None:
        return sum(self.reactions) / len(self.reactions) if self.reactions else None


class Database:
    def __init__(self, path: Path | str):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.migrate()

    def migrate(self) -> None:
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        for index in range(version, len(MIGRATIONS)):
            with self.conn:
                self.conn.executescript(MIGRATIONS[index])
                self.conn.execute(f"PRAGMA user_version = {index + 1}")

    @property
    def schema_version(self) -> int:
        return self.conn.execute("PRAGMA user_version").fetchone()[0]

    def close(self) -> None:
        self.conn.close()

    # settings
    def get(self, key: str):
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return DEFAULTS.get(key)
        try:
            return json.loads(row[0])
        except ValueError:
            return DEFAULTS.get(key)

    def set(self, key: str, value) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, json.dumps(value, ensure_ascii=False)),
            )

    # PIN
    def has_pin(self) -> bool:
        return bool(self.get("pin_hash"))

    def set_pin(self, pin: str) -> None:
        salt = os.urandom(16).hex()
        self.set("pin_salt", salt)
        self.set("pin_hash", _hash_pin(pin, salt))

    def check_pin(self, pin: str) -> bool:
        return self.has_pin() and _hash_pin(pin, self.get("pin_salt")) == self.get("pin_hash")

    # sessions
    def start_session(self, planned_s: int) -> int:
        with self.conn:
            cur = self.conn.execute("INSERT INTO sessions(started, planned_s) VALUES(?, ?)", (time.time(), planned_s))
        return cur.lastrowid

    def update_session(self, session_id: int, active_s: float, ended: bool = False) -> None:
        with self.conn:
            if ended:
                self.conn.execute(
                    "UPDATE sessions SET active_s = ?, ended = ? WHERE id = ?", (active_s, time.time(), session_id)
                )
            else:
                self.conn.execute("UPDATE sessions SET active_s = ? WHERE id = ?", (active_s, session_id))

    def minutes_today(self, now: float | None = None) -> float:
        now = now or time.time()
        start = dt.datetime.fromtimestamp(now).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        row = self.conn.execute("SELECT COALESCE(SUM(active_s), 0) FROM sessions WHERE started >= ?", (start,)).fetchone()
        return row[0] / 60.0

    # breaks
    def start_break(self, seconds: int) -> None:
        now = time.time()
        with self.conn:
            self.conn.execute("UPDATE breaks SET done = 1 WHERE done = 0")
            self.conn.execute("INSERT INTO breaks(started, until) VALUES(?, ?)", (now, now + seconds))

    def pending_break(self, now: float | None = None) -> float:
        """Сколько секунд обязательного перерыва осталось (0 — перерыва нет)."""
        now = now or time.time()
        row = self.conn.execute("SELECT until FROM breaks WHERE done = 0 ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            return 0.0
        return max(0.0, row[0] - now)

    def finish_break(self) -> None:
        with self.conn:
            self.conn.execute("UPDATE breaks SET done = 1 WHERE done = 0")

    # attempts / progress
    def record_attempt(self, session_id: int | None, workshop: str, exercise: str, level: int, r: LevelResult) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO attempts(session_id, ts, workshop, exercise, level, success, stars, duration_ms,"
                " err_impulsive, err_sequence, err_omission, reaction_ms) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    session_id, time.time(), workshop, exercise, level, int(r.success), r.stars, r.duration_ms,
                    r.err_impulsive, r.err_sequence, r.err_omission, r.reaction_ms,
                ),
            )
            row = self.conn.execute("SELECT level, fails FROM progress WHERE exercise = ?", (exercise,)).fetchone()
            cur_level, fails = (row["level"], row["fails"]) if row else (level, 0)
            if r.success and r.stars >= 2:
                cur_level, fails = min(MAX_LEVEL, level + 1), 0
            elif r.success:
                cur_level, fails = level, 0
            else:
                fails += 1
                if fails >= 2:
                    cur_level, fails = max(1, level - 1), 0
                else:
                    cur_level = level
            self.conn.execute(
                "INSERT INTO progress(exercise, level, fails) VALUES(?,?,?) "
                "ON CONFLICT(exercise) DO UPDATE SET level = excluded.level, fails = excluded.fails",
                (exercise, cur_level, fails),
            )

    def level_for(self, exercise: str) -> int:
        row = self.conn.execute("SELECT level FROM progress WHERE exercise = ?", (exercise,)).fetchone()
        return row["level"] if row else 1

    def total_stars(self) -> int:
        return self.conn.execute("SELECT COALESCE(SUM(stars), 0) FROM attempts").fetchone()[0]

    # statistics
    def weekly_stats(self, weeks: int = 8, now: float | None = None) -> list[dict]:
        now_d = dt.date.fromtimestamp(now or time.time())
        monday = now_d - dt.timedelta(days=now_d.weekday())
        result = []
        for i in range(weeks - 1, -1, -1):
            start_d = monday - dt.timedelta(weeks=i)
            start = dt.datetime.combine(start_d, dt.time()).timestamp()
            end = start + 7 * 86400
            s = self.conn.execute(
                "SELECT COUNT(*) n, COALESCE(SUM(active_s), 0) active FROM sessions WHERE started >= ? AND started < ?",
                (start, end),
            ).fetchone()
            a = self.conn.execute(
                "SELECT COUNT(*) n, COALESCE(SUM(duration_ms), 0) focus, COALESCE(SUM(err_impulsive), 0) imp,"
                " COALESCE(SUM(err_sequence), 0) seq, COALESCE(SUM(err_omission), 0) om, COALESCE(SUM(stars), 0) stars,"
                " COALESCE(SUM(success), 0) ok, AVG(reaction_ms) rt FROM attempts WHERE ts >= ? AND ts < ?",
                (start, end),
            ).fetchone()
            levels = a["n"] or 0
            result.append(
                {
                    "week_start": start_d,
                    "sessions": s["n"],
                    "minutes": s["active"] / 60.0,
                    "levels": levels,
                    "focus_min_per_session": (a["focus"] / 60000.0 / s["n"]) if s["n"] else 0.0,
                    "avg_focus_s": (a["focus"] / 1000.0 / levels) if levels else 0.0,
                    "err_impulsive": a["imp"],
                    "err_sequence": a["seq"],
                    "err_omission": a["om"],
                    "stars": a["stars"],
                    "success_rate": (a["ok"] / levels) if levels else 0.0,
                    "reaction_ms": a["rt"],
                }
            )
        return result

    def exercise_stats(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT workshop, exercise, COUNT(*) n, MAX(level) max_level, SUM(stars) stars, AVG(duration_ms) dur,"
            " SUM(err_impulsive) imp, SUM(err_sequence) seq, SUM(err_omission) om, AVG(reaction_ms) rt"
            " FROM attempts GROUP BY workshop, exercise ORDER BY workshop, exercise"
        ).fetchall()
        return [dict(r) | {"level": self.level_for(r["exercise"])} for r in rows]

    def export_json(self) -> dict:
        def rows(sql: str) -> list[dict]:
            return [dict(r) for r in self.conn.execute(sql).fetchall()]

        return {
            "schema_version": self.schema_version,
            "exported": time.time(),
            "sessions": rows("SELECT * FROM sessions ORDER BY id"),
            "attempts": rows("SELECT * FROM attempts ORDER BY id"),
            "progress": rows("SELECT * FROM progress ORDER BY exercise"),
        }

    def reset_progress(self) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM attempts")
            self.conn.execute("DELETE FROM sessions")
            self.conn.execute("DELETE FROM progress")
            self.conn.execute("DELETE FROM breaks")


def _hash_pin(pin: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt or "00"), 100_000).hex()
