import ast
import re
from pathlib import Path

from mv.phrases import PHRASES, PRAISE, RETRY, WARMUPS

ROOT = Path(__file__).resolve().parents[1]


def test_no_network_code():
    banned = re.compile(r"\b(import (socket|urllib|requests|http)|from (socket|urllib|requests|http)|QNetwork)")
    for path in (ROOT / "mv").rglob("*.py"):
        assert not banned.search(path.read_text(encoding="utf-8")), path


def test_phrase_keys_exist():
    used = set()
    for path in (ROOT / "mv").rglob("*.py"):
        for m in re.finditer(r"""(?:say|intro\s*=\s*\[|\.say\(\[?)\s*["']([a-z_0-9]+)["']""", path.read_text(encoding="utf-8")):
            used.add(m.group(1))
    for key in used | set(PRAISE) | set(RETRY) | set(WARMUPS):
        assert key in PHRASES, key


def test_python_syntax():
    for path in (ROOT / "mv").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))


def test_pdf_export(db, app, tmp_path):
    from mv.db import LevelResult
    from mv.report import export_pdf

    sid = db.start_session(420)
    db.record_attempt(sid, "calm", "breathing", 1, LevelResult(True, 3, 60000))
    out = tmp_path / "r.pdf"
    export_pdf(db, str(out), {"breathing": "Дыхание"})
    assert out.read_bytes()[:4] == b"%PDF" and out.stat().st_size > 2000


def test_translations_complete():
    import sys

    sys.path.insert(0, str(ROOT / "tools"))
    import i18n

    strings = i18n.extract()
    for lang in i18n.LANGS:
        tr = i18n.load(ROOT / "mv" / "i18n" / f"{lang}.ts")
        for ctx, sources in strings.items():
            for src in sources:
                assert (ctx, src) in tr, (lang, ctx, src)
        assert (ROOT / "mv" / "i18n" / f"{lang}.qm").exists()


def test_voice_files():
    for lang in ("ru", "en", "zh"):
        for key in PHRASES:
            assert (ROOT / "mv" / "data" / "voice" / lang / f"{key}.ogg").exists(), (lang, key)


def test_detect_language(monkeypatch):
    from mv.i18n import detect_language

    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    assert detect_language() == "en"
    monkeypatch.setenv("LANG", "zh_CN.UTF-8")
    assert detect_language() == "zh"
    monkeypatch.setenv("LANG", "C.UTF-8")
    assert detect_language() == "ru"
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    assert detect_language() == "ru"
