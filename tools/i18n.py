"""Обновление переводов.

  python tools/i18n.py update   — собрать строки из кода в mv/i18n/{en,zh}.ts (переводы сохраняются)
  python tools/i18n.py release  — скомпилировать .ts → .qm
  python tools/i18n.py check    — проверить, что всё переведено
"""
from __future__ import annotations

import ast
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "mv" / "i18n"
LANGS = {"en": "en_US", "zh": "zh_CN"}
sys.path.insert(0, str(ROOT))


def extract() -> dict[str, list[str]]:
    app: list[str] = []
    for path in sorted((ROOT / "mv").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("tr", "N_")
                    and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                app.append(node.args[0].value)
    from mv import APP_NAME, AUTHOR
    from mv.phrases import PHRASES

    app += [APP_NAME, AUTHOR]
    return {"app": list(dict.fromkeys(app)), "voice": list(dict.fromkeys(PHRASES.values()))}


def load(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    out = {}
    for ctx in ET.parse(path).getroot().iter("context"):
        name = ctx.findtext("name")
        for msg in ctx.iter("message"):
            tr = msg.find("translation")
            if tr is not None and tr.text and tr.get("type") not in ("obsolete", "vanished"):
                out[(name, msg.findtext("source"))] = tr.text
    return out


def save(path: Path, lang: str, strings: dict[str, list[str]], translations: dict[tuple[str, str], str]) -> int:
    root = ET.Element("TS", version="2.1", language=LANGS[lang], sourcelanguage="ru_RU")
    missing = 0
    for ctx_name, sources in strings.items():
        ctx = ET.SubElement(root, "context")
        ET.SubElement(ctx, "name").text = ctx_name
        for src in sources:
            msg = ET.SubElement(ctx, "message")
            ET.SubElement(msg, "source").text = src
            t = ET.SubElement(msg, "translation")
            value = translations.get((ctx_name, src))
            if value:
                t.text = value
            else:
                t.set("type", "unfinished")
                missing += 1
    ET.indent(root)
    path.write_text('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n' + ET.tostring(root, encoding="unicode") + "\n",
                    encoding="utf-8")
    return missing


def update(extra: dict[str, dict[tuple[str, str], str]] | None = None) -> int:
    strings = extract()
    missing = 0
    for lang in LANGS:
        path = I18N / f"{lang}.ts"
        tr = load(path)
        if extra:
            tr.update(extra.get(lang, {}))
        m = save(path, lang, strings, tr)
        print(f"{lang}: {sum(len(v) for v in strings.values())} strings, {m} untranslated")
        missing += m
    return missing


def release() -> None:
    lrelease = Path(sys.executable).with_name("pyside6-lrelease")
    cmd = str(lrelease) if lrelease.exists() else "pyside6-lrelease"
    for lang in LANGS:
        subprocess.run([cmd, "-silent", str(I18N / f"{lang}.ts"), "-qm", str(I18N / f"{lang}.qm")], check=True)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "update"
    if action == "update":
        update()
    elif action == "release":
        release()
    elif action == "check":
        sys.exit(1 if update() else 0)
