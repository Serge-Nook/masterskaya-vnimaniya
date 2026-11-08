import time

from mv.db import DEFAULTS, MIGRATIONS, Database, LevelResult


def test_migrations_and_defaults(db, tmp_path):
    assert db.schema_version == len(MIGRATIONS)
    for k, v in DEFAULTS.items():
        assert db.get(k) == v
    db.set("session_minutes", 9)
    db.close()
    again = Database(tmp_path / "t.sqlite3")
    assert again.get("session_minutes") == 9
    assert again.schema_version == len(MIGRATIONS)
    again.close()


def test_pin(db):
    assert not db.has_pin()
    db.set_pin("2468")
    assert db.has_pin()
    assert db.check_pin("2468")
    assert not db.check_pin("1111")
    assert "2468" not in str(db.get("pin_hash"))


def test_level_progression(db):
    ok = LevelResult(True, 3, 1000)
    fail = LevelResult(False, 0, 1000, err_impulsive=2)
    assert db.level_for("maze") == 1
    db.record_attempt(None, "planning", "maze", 1, ok)
    assert db.level_for("maze") == 2
    db.record_attempt(None, "planning", "maze", 2, fail)
    assert db.level_for("maze") == 2
    db.record_attempt(None, "planning", "maze", 2, fail)
    assert db.level_for("maze") == 1
    assert db.total_stars() == 3


def test_sessions_breaks_and_stats(db):
    sid = db.start_session(420)
    db.update_session(sid, 300)
    db.record_attempt(sid, "attention", "red_circles", 1,
                      LevelResult(True, 2, 30000, err_impulsive=1, err_sequence=2, reactions=[500, 700]))
    assert abs(db.minutes_today() - 5) < 1e-6
    week = db.weekly_stats(4)[-1]
    assert week["sessions"] == 1 and week["levels"] == 1
    assert week["err_impulsive"] == 1 and week["err_sequence"] == 2
    assert week["reaction_ms"] == 600
    assert db.exercise_stats()[0]["exercise"] == "red_circles"
    db.start_break(60)
    assert 0 < db.pending_break() <= 60
    assert db.pending_break(time.time() + 120) == 0
    db.finish_break()
    assert db.pending_break() == 0
    data = db.export_json()
    assert len(data["attempts"]) == 1 and len(data["sessions"]) == 1
    db.reset_progress()
    assert db.total_stars() == 0 and db.export_json()["sessions"] == []
