"""Режим взрослого: PIN, настройки, статистика, данные, о программе."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QScrollArea, QSlider, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from mv import APP_NAME, AUTHOR, AUTHOR_SITE, __version__, theme
from mv.exercises.registry import EXERCISES, WORKSHOPS
from mv.i18n import LANGUAGES, tr
from mv.paths import documents_dir, user_data_dir
from mv.report import draw_bar_chart, draw_errors_chart, export_pdf
from mv.widgets import Screen, make_button


class PinScreen(Screen):
    """Ввод PIN крупной экранной клавиатурой (мышь, тач, геймпад)."""

    def __init__(self, ctx):
        super().__init__(ctx)
        self.value = ""
        self.first = ""
        self.title = QLabel("")
        self.title.setObjectName("Title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint = QLabel("")
        self.hint.setObjectName("Subtitle")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setWordWrap(True)
        self.dots = QLabel("")
        self.dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dots.setStyleSheet("QLabel { font-size: 54px; letter-spacing: 16px; min-height: 70px; }")
        grid = QGridLayout()
        grid.setSpacing(14)
        self.keys = []
        labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "⌫", "0", "OK"]
        for i, t in enumerate(labels):
            b = make_button(t, primary=(t == "OK"), slot=lambda _=False, t=t: self.press(t))
            b.setFixedSize(130, 90)
            b.setStyleSheet("font-size: 34px;")
            grid.addWidget(b, i // 3, i % 3)
            self.keys.append(b)
        back = make_button(tr("Назад"), slot=self.back)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 20, 40, 30)
        top = QHBoxLayout()
        top.addWidget(back)
        top.addStretch(1)
        lay.addLayout(top)
        lay.addWidget(self.title)
        lay.addWidget(self.hint)
        lay.addWidget(self.dots)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addLayout(grid)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addStretch(1)

    def on_enter(self):
        self.value = ""
        self.first = ""
        self.creating = not self.ctx.db.has_pin()
        self.title.setText(tr("Для взрослых"))
        self.hint.setText(tr("Придумайте PIN-код из 4 цифр. Он защищает настройки и статистику.")
                          if self.creating else tr("Введите PIN-код"))
        self._dots()

    def first_focus(self):
        return self.keys[0]

    def _dots(self):
        self.dots.setText("●" * len(self.value) + "○" * (4 - len(self.value)))

    def press(self, t: str):
        if t == "⌫":
            self.value = self.value[:-1]
        elif t == "OK":
            self.submit()
            return
        elif len(self.value) < 4:
            self.value += t
        self._dots()
        if len(self.value) == 4 and not self.creating:
            QTimer.singleShot(150, self.submit)

    def submit(self):
        if len(self.value) != 4:
            return
        if self.creating:
            if not self.first:
                self.first = self.value
                self.value = ""
                self.hint.setText(tr("Повторите PIN-код"))
            elif self.first == self.value:
                self.ctx.db.set_pin(self.value)
                self.ctx.window.show_adult_panel()
            else:
                self.first = ""
                self.value = ""
                self.hint.setText(tr("PIN-коды не совпали. Придумайте PIN-код ещё раз."))
        elif self.ctx.db.check_pin(self.value):
            self.ctx.window.show_adult_panel()
        else:
            self.value = ""
            self.hint.setText(tr("Неверный PIN-код. Попробуйте ещё раз."))
        self._dots()

    def back(self):
        self.ctx.window.leave_adult()


class ChartView(QWidget):
    def __init__(self, ctx, kind: str):
        super().__init__()
        self.ctx = ctx
        self.kind = kind
        self.weeks: list[dict] = []
        self.setMinimumHeight(300)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = p.font()
        f.setPixelSize(16)
        p.setFont(f)
        r = QRectF(4, 4, self.width() - 8, self.height() - 8)
        if self.kind == "minutes":
            draw_bar_chart(p, r, self.weeks, "minutes", tr("Минут в неделю"), theme.ACCENT, lambda v: f"{v:.0f}")
        elif self.kind == "focus":
            draw_bar_chart(p, r, self.weeks, "avg_focus_s", tr("Концентрация на уровне, с"), theme.BLUE, lambda v: f"{v:.0f}")
        else:
            draw_errors_chart(p, r, self.weeks)
        p.end()


def exercise_titles() -> dict[str, str]:
    return {k: tr(cls.title) for k, cls in EXERCISES.items()}


class AdultScreen(Screen):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._scroll(self._settings_tab()), tr("Настройки"))
        self.tabs.addTab(self._scroll(self._stats_tab()), tr("Статистика"))
        self.tabs.addTab(self._scroll(self._data_tab()), tr("Данные"))
        self.tabs.addTab(self._scroll(self._about_tab()), tr("О программе"))
        title = QLabel(tr("Для взрослых"))
        title.setObjectName("Title")
        back = make_button(tr("Вернуться к игре"), primary=True, slot=self.back)
        top = QHBoxLayout()
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(back)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.addLayout(top)
        lay.addWidget(self.tabs, 1)

    @staticmethod
    def _scroll(w: QWidget) -> QScrollArea:
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setWidget(w)
        return s

    # настройки
    def _spin(self, key, lo, hi, suffix=""):
        s = QSpinBox()
        s.setRange(lo, hi)
        s.setSuffix(suffix)
        s.setValue(int(self.ctx.db.get(key)))
        s.valueChanged.connect(lambda v: self._set(key, v))
        return s

    def _check(self, key, text):
        c = QCheckBox(text)
        c.setChecked(bool(self.ctx.db.get(key)))
        c.toggled.connect(lambda v: self._set(key, v))
        return c

    def _set(self, key, value):
        self.ctx.db.set(key, value)
        if key in ("volume", "volume_cap", "music", "voice"):
            if key == "volume_cap" and int(self.ctx.db.get("volume")) > value:
                self.volume.setValue(value)
            self.volume.setMaximum(int(self.ctx.db.get("volume_cap")))
            self.ctx.audio.apply_volume()
        if key == "fullscreen":
            self.ctx.window.apply_fullscreen()

    def _settings_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(30, 24, 30, 24)
        form.setVerticalSpacing(16)
        form.setHorizontalSpacing(30)
        db = self.ctx.db
        form.addRow(tr("Длительность занятия"), self._spin("session_minutes", 5, 10, " " + tr("мин")))
        form.addRow(tr("Перерыв (разминка)"), self._spin("break_minutes", 1, 10, " " + tr("мин")))
        form.addRow(tr("Лимит в день (0 — без лимита)"), self._spin("daily_limit_minutes", 0, 120, " " + tr("мин")))
        levels = [tr("Легко"), tr("Средне"), tr("Сложнее")]
        for ws in WORKSHOPS:
            c = QComboBox()
            c.addItems(levels)
            key = f"difficulty_{ws['key']}"
            c.setCurrentIndex(int(db.get(key)) - 1)
            c.currentIndexChanged.connect(lambda i, k=key: self._set(k, i + 1))
            form.addRow(tr("Сложность: %1").replace("%1", tr(ws["title"])), c)
        form.addRow(tr("Циклов дыхания"), self._spin("breath_cycles", 10, 15))
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, int(db.get("volume_cap")))
        self.volume.setValue(min(int(db.get("volume")), int(db.get("volume_cap"))))
        self.volume.valueChanged.connect(lambda v: self._set("volume", v))
        form.addRow(tr("Громкость"), self.volume)
        form.addRow(tr("Предел громкости"), self._spin("volume_cap", 10, 70, " %"))
        form.addRow("", self._check("voice", tr("Голос Тихона")))
        form.addRow("", self._check("music", tr("Спокойная музыка")))
        form.addRow("", self._check("fullscreen", tr("Полноэкранный режим")))
        reward = QComboBox()
        reward.addItems([tr("Сад"), tr("Аквариум")])
        reward.setCurrentIndex(0 if db.get("reward") == "garden" else 1)
        reward.currentIndexChanged.connect(lambda i: self._set("reward", "garden" if i == 0 else "aquarium"))
        form.addRow(tr("Награда за звёздочки"), reward)
        lang = QComboBox()
        codes = list(LANGUAGES)
        lang.addItems([LANGUAGES[c] for c in codes])
        from mv.i18n import current_language

        lang.setCurrentIndex(codes.index(current_language()) if current_language() in codes else 0)
        lang.currentIndexChanged.connect(lambda i: self._change_language(codes[i]))
        form.addRow(tr("Язык"), lang)
        form.addRow("", make_button(tr("Сменить PIN-код"), slot=self._change_pin))
        form.addRow("", make_button(tr("Снять дневной лимит на сегодня"), slot=self._lift_limit))
        form.addRow("", make_button(tr("Отменить текущий перерыв"), slot=self._cancel_break))
        return w

    def _change_language(self, code):
        self.ctx.db.set("language", code)
        self.ctx.window.reload_language()

    def _change_pin(self):
        self.ctx.db.set("pin_hash", "")
        self.ctx.window.open_adult()

    def _lift_limit(self):
        self.ctx.db.set("limit_lifted_on", dt.date.today().isoformat())
        self._info(tr("Лимит на сегодня снят."))

    def _cancel_break(self):
        self.ctx.db.finish_break()
        self._info(tr("Перерыв отменён."))

    def _info(self, text):
        QMessageBox.information(self, tr(APP_NAME), text)

    # статистика
    def _stats_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 20, 20, 20)
        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        lay.addWidget(self.summary)
        row = QHBoxLayout()
        self.charts = [ChartView(self.ctx, "minutes"), ChartView(self.ctx, "focus")]
        for c in self.charts:
            row.addWidget(c)
        lay.addLayout(row)
        errors = ChartView(self.ctx, "errors")
        self.charts.append(errors)
        lay.addWidget(errors)
        self.table = QTableWidget()
        self.table.setMinimumHeight(360)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.table)
        return w

    def refresh_stats(self):
        weeks = self.ctx.db.weekly_stats(8)
        for c in self.charts:
            c.weeks = weeks
            c.update()
        this = weeks[-1]
        self.summary.setText(
            "<b>" + tr("Эта неделя") + ":</b> "
            + tr("занятий %1, минут %2, уровней %3, успешно %4%").replace("%1", str(this["sessions"]))
            .replace("%2", f"{this['minutes']:.0f}").replace("%3", str(this["levels"]))
            .replace("%4", f"{this['success_rate'] * 100:.0f}")
            + "<br>" + tr("Сегодня: %1 мин из %2").replace("%1", f"{self.ctx.db.minutes_today():.0f}")
            .replace("%2", str(self.ctx.db.get("daily_limit_minutes") or "∞"))
        )
        cols = [tr("Упражнение"), tr("Уровень"), tr("Попыток"), tr("Звёзд"), tr("Импульсивные"),
                tr("Последовательность"), tr("Пропуски"), tr("Реакция, мс")]
        stats = self.ctx.db.exercise_stats()
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setRowCount(len(stats))
        titles = exercise_titles()
        for r, s in enumerate(stats):
            vals = [titles.get(s["exercise"], s["exercise"]), s["level"], s["n"], s["stars"] or 0, s["imp"] or 0,
                    s["seq"] or 0, s["om"] or 0, f"{s['rt']:.0f}" if s["rt"] else "—"]
            for c, v in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    # данные
    def _data_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(30, 24, 30, 24)
        lay.setSpacing(16)
        info = QLabel(tr("Все данные хранятся только на этом компьютере:") + f"<br><code>{user_data_dir()}</code>")
        info.setWordWrap(True)
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(info)
        for text, slot in ((tr("Сохранить статистику в PDF"), self.save_pdf),
                           (tr("Экспорт данных (JSON)"), self.save_json),
                           (tr("Сбросить прогресс и статистику"), self.reset)):
            b = make_button(text, slot=slot)
            lay.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
        lay.addStretch(1)
        return w

    def _ask_path(self, name: str, flt: str) -> str:
        default = str(documents_dir() / name)
        path, _ = QFileDialog.getSaveFileName(self, tr(APP_NAME), default, flt)
        return path

    def save_pdf(self):
        name = f"masterskaya-vnimaniya-{dt.date.today().isoformat()}.pdf"
        path = self._ask_path(name, "PDF (*.pdf)")
        if path:
            export_pdf(self.ctx.db, path, exercise_titles())
            self._info(tr("Отчёт сохранён:") + "\n" + path)

    def save_json(self):
        name = f"masterskaya-vnimaniya-{dt.date.today().isoformat()}.json"
        path = self._ask_path(name, "JSON (*.json)")
        if path:
            Path(path).write_text(json.dumps(self.ctx.db.export_json(), ensure_ascii=False, indent=2), encoding="utf-8")
            self._info(tr("Данные сохранены:") + "\n" + path)

    def reset(self):
        ans = QMessageBox.question(self, tr(APP_NAME), tr("Удалить весь прогресс, звёздочки и статистику? Это нельзя отменить."))
        if ans == QMessageBox.StandardButton.Yes:
            self.ctx.db.reset_progress()
            self.refresh_stats()
            self._info(tr("Прогресс сброшен."))

    # о программе
    def _about_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(30, 24, 30, 24)
        text = QLabel(
            f"<h2>{tr(APP_NAME)}</h2>"
            f"<p>{tr('Версия')} {__version__}</p>"
            f"<p>{tr('Автор')}: {tr(AUTHOR)}<br>{tr('Сайт')}: nookbat.ru</p>"
            "<p>" + tr("Вспомогательный тренажёр внимания, сдержанности и саморегуляции для детей 6–7 лет."
                       " Не заменяет консультацию специалиста.") + "</p>"
            "<p>" + tr("Работает без интернета. Не собирает и не передаёт данные.") + "</p>"
            "<p>" + tr("Шрифт Nunito — SIL Open Font License. Голос — Piper TTS.") + "</p>"
        )
        text.setWordWrap(True)
        lay.addWidget(text)
        lay.addStretch(1)
        return w

    def on_enter(self):
        self.refresh_stats()

    def back(self):
        self.ctx.window.leave_adult()
