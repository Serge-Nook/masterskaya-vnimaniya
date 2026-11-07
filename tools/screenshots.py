"""Снимки всех экранов без дисплея: QT_QPA_PLATFORM=offscreen python tools/screenshots.py out_dir [lang]"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import mv.main as m  # noqa: E402
from mv.db import LevelResult  # noqa: E402
from mv.exercises.registry import EXERCISES  # noqa: E402

out = Path(sys.argv[1] if len(sys.argv) > 1 else "shots")
lang = sys.argv[2] if len(sys.argv) > 2 else "ru"
out.mkdir(parents=True, exist_ok=True)
steps = []


def step(fn):
    steps.append(fn)
    return fn


def shot(name):
    QApplication.processEvents()
    w = QApplication.activeWindow() or win[0]
    w.grab().save(str(out / f"{name}.png"))


win = []
orig_init = m.MainWindow.__init__


def init(self, ctx):
    orig_init(self, ctx)
    win.append(self)
    db = ctx.db
    import random
    import time
    rng = random.Random(1)
    now = time.time()
    for d in range(40):
        sid = db.start_session(420)
        db.conn.execute("UPDATE sessions SET started=?, active_s=? WHERE id=?", (now - d * 86400 * 1.3, rng.randint(200, 420), sid))
        for k in list(EXERCISES)[: rng.randint(2, 6)]:
            db.record_attempt(sid, EXERCISES[k].workshop, k, 1, LevelResult(True, rng.randint(1, 3), rng.randint(20000, 90000),
                              rng.randint(0, 3), rng.randint(0, 2), rng.randint(0, 2), [rng.uniform(400, 900)]))
        db.conn.execute("UPDATE attempts SET ts=? WHERE session_id=?", (now - d * 86400 * 1.3, sid))
    db.conn.commit()
    QTimer.singleShot(500, run)


m.MainWindow.__init__ = init


def run():
    w = win[0]
    seq = [
        ("01_disclaimer", lambda: None),
        ("02_home", lambda: w.screens["disclaimer"]._accept()),
        ("03_ws_attention", lambda: w.open_workshop("attention")),
        ("04_ws_planning", lambda: w.open_workshop("planning")),
        ("05_ws_calm", lambda: w.open_workshop("calm")),
    ]
    for key, cls in EXERCISES.items():
        seq.append((f"10_{key}_intro", lambda cls=cls: w.start_exercise(cls)))
        seq.append((f"11_{key}_play", lambda: w.current.run_level()))
        seq.append((f"11_{key}_play2", lambda: None))
        seq.append((f"12_{key}_done", lambda: w.current.ex.finish(True, 3)))
    seq += [
        ("20_garden", lambda: w.open_garden()),
        ("21_break", lambda: w.start_break()),
        ("22_break_card", lambda: w.current.panel.proceed.emit()),
        ("30_pin", lambda: w.open_adult()),
        ("31_adult_settings", lambda: [w.current.press(c) for c in ["1","2","3","4","OK","1","2","3","4","OK"]]),
        ("32_adult_stats", lambda: w.current.tabs.setCurrentIndex(1)),
        ("33_adult_data", lambda: w.current.tabs.setCurrentIndex(2)),
        ("34_adult_about", lambda: w.current.tabs.setCurrentIndex(3)),
    ]

    def go(i=0):
        if i >= len(seq):
            from mv.report import export_pdf
            from mv.screens.adult import exercise_titles
            export_pdf(w.ctx.db, str(out / "report.pdf"), exercise_titles())
            QApplication.quit()
            return
        name, fn = seq[i]
        fn()
        delay = 1200 if name.endswith("_play2") else 700
        QTimer.singleShot(delay, lambda: (shot(name), go(i + 1)))

    go()


sys.exit(m.main(["--windowed", "--lang", lang]))
