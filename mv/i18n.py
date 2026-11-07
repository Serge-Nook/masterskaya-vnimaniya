from __future__ import annotations

import locale
import os

from PySide6.QtCore import QCoreApplication, QLibraryInfo, QLocale, QTranslator

from mv.paths import I18N

LANGUAGES = {"ru": "Русский", "en": "English", "zh": "中文"}
_translators: list[QTranslator] = []
_current = "ru"


def N_(text: str) -> str:
    """Помечает строку для перевода, не переводя её сразу."""
    return text


def tr(text: str) -> str:
    return QCoreApplication.translate("app", text)


def tr_voice(text: str) -> str:
    return QCoreApplication.translate("voice", text)


def detect_language() -> str:
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var, "")
        if value:
            code = value[:2].lower()
            return code if code in LANGUAGES else "en"
    try:
        code = (locale.getlocale()[0] or "ru")[:2].lower()
    except ValueError:
        code = "ru"
    return code if code in LANGUAGES else "ru"


def current_language() -> str:
    return _current


def install_language(lang: str) -> str:
    global _current
    app = QCoreApplication.instance()
    for t in _translators:
        app.removeTranslator(t)
    _translators.clear()
    if lang not in LANGUAGES:
        lang = "ru"
    _current = lang
    if lang != "ru":
        t = QTranslator()
        if t.load(str(I18N / f"{lang}.qm")):
            app.installTranslator(t)
            _translators.append(t)
    qt = QTranslator()
    qt_lang = {"ru": "ru", "en": "en", "zh": "zh_CN"}[lang]
    if qt.load(QLocale(qt_lang), "qtbase", "_", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(qt)
        _translators.append(qt)
    return lang
