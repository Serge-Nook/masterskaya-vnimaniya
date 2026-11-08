"""Графики статистики и PDF-отчёт для взрослого."""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QMarginsF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPageLayout, QPageSize, QPainter, QPdfWriter, QPen

from mv import APP_NAME, AUTHOR, AUTHOR_SITE, __version__, theme
from mv.i18n import N_, tr

ERROR_SERIES = [
    ("err_impulsive", N_("Импульсивные"), theme.RED),
    ("err_sequence", N_("Последовательность"), theme.BLUE),
    ("err_omission", N_("Пропуски"), theme.ORANGE),
]


def week_label(d: dt.date) -> str:
    return d.strftime("%d.%m")


def draw_bar_chart(p: QPainter, rect: QRectF, weeks: list[dict], key: str, title: str, color: QColor,
                   fmt=lambda v: f"{v:.1f}") -> None:
    _frame(p, rect, title)
    area = rect.adjusted(50, 50, -16, -40)
    values = [float(w[key] or 0) for w in weeks]
    top = max(values + [1.0]) * 1.15
    _axes(p, area, top, fmt)
    n = len(weeks)
    bw = area.width() / max(1, n)
    f = p.font()
    for i, (w, v) in enumerate(zip(weeks, values)):
        h = area.height() * v / top
        r = QRectF(area.left() + i * bw + bw * 0.18, area.bottom() - h, bw * 0.64, h)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawRoundedRect(r, 4, 4)
        p.setPen(theme.INK_SOFT)
        _font(p, 0.75)
        p.drawText(QRectF(area.left() + i * bw, area.bottom() + 4, bw, 30), Qt.AlignmentFlag.AlignHCenter, week_label(w["week_start"]))
        if v > 0:
            p.setPen(theme.INK)
            p.drawText(QRectF(r.left() - 20, r.top() - 26, r.width() + 40, 24), Qt.AlignmentFlag.AlignHCenter, fmt(v))
        p.setFont(f)


def draw_errors_chart(p: QPainter, rect: QRectF, weeks: list[dict]) -> None:
    _frame(p, rect, tr("Ошибки по типам"))
    area = rect.adjusted(50, 50, -16, -70)
    totals = [sum(w[k] for k, _, _ in ERROR_SERIES) for w in weeks]
    top = max(totals + [1]) * 1.15
    _axes(p, area, top, lambda v: f"{v:.0f}")
    bw = area.width() / max(1, len(weeks))
    f = p.font()
    for i, w in enumerate(weeks):
        y = area.bottom()
        for k, _, color in ERROR_SERIES:
            h = area.height() * w[k] / top
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawRect(QRectF(area.left() + i * bw + bw * 0.18, y - h, bw * 0.64, h))
            y -= h
        p.setPen(theme.INK_SOFT)
        _font(p, 0.75)
        p.drawText(QRectF(area.left() + i * bw, area.bottom() + 4, bw, 30), Qt.AlignmentFlag.AlignHCenter, week_label(w["week_start"]))
        p.setFont(f)
    x = area.left()
    _font(p, 0.8)
    for _, label, color in ERROR_SERIES:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawRect(QRectF(x, rect.bottom() - 30, 18, 18))
        p.setPen(theme.INK)
        text = tr(label)
        p.drawText(QPointF(x + 26, rect.bottom() - 15), text)
        x += 40 + p.fontMetrics().horizontalAdvance(text)
    p.setFont(f)


def _font(p: QPainter, scale: float) -> None:
    f = QFont(p.font())
    f.setPointSizeF(max(5.0, f.pointSizeF() * scale)) if f.pointSizeF() > 0 else f.setPixelSize(max(8, int(f.pixelSize() * scale)))
    p.setFont(f)


def _frame(p: QPainter, rect: QRectF, title: str) -> None:
    p.setPen(QPen(theme.ACCENT_LIGHT, 2))
    p.setBrush(QColor("white"))
    p.drawRoundedRect(rect, 12, 12)
    p.setPen(theme.INK)
    f = QFont(p.font())
    f.setBold(True)
    p.save()
    p.setFont(f)
    p.drawText(rect.adjusted(16, 10, -16, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, title)
    p.restore()


def _axes(p: QPainter, area: QRectF, top: float, fmt) -> None:
    p.setPen(QPen(QColor("#E3ECE8"), 1))
    f = p.font()
    _font(p, 0.75)
    for k in range(5):
        y = area.bottom() - area.height() * k / 4
        p.setPen(QPen(QColor("#E3ECE8"), 1))
        p.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
        p.setPen(theme.INK_SOFT)
        p.drawText(QRectF(area.left() - 48, y - 12, 44, 24), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, fmt(top * k / 4))
    p.setFont(f)


def export_pdf(db, path: str, exercise_titles: dict[str, str]) -> None:
    weeks = db.weekly_stats(8)
    writer = QPdfWriter(path)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait, QMarginsF(15, 15, 15, 15)))
    writer.setResolution(150)
    writer.setTitle(tr(APP_NAME) + " — " + tr("статистика"))
    writer.setCreator(f"{tr(APP_NAME)} {__version__}")
    p = QPainter(writer)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    W = writer.width()
    f = QFont("Nunito")
    f.setPointSizeF(10)
    p.setFont(f)
    y = 0.0

    def heading(text, size=18):
        nonlocal y
        hf = QFont(f)
        hf.setPointSizeF(size)
        hf.setBold(True)
        p.setFont(hf)
        p.setPen(theme.INK)
        h = p.fontMetrics().height() * 1.4
        p.drawText(QRectF(0, y, W, h), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
        y += h
        p.setFont(f)

    heading(tr(APP_NAME) + " — " + tr("статистика занятий"), 18)
    p.setPen(theme.INK_SOFT)
    lh = p.fontMetrics().height() * 1.3
    p.drawText(QRectF(0, y, W, lh), Qt.AlignmentFlag.AlignLeft,
               tr("Сформировано: %1").replace("%1", dt.datetime.now().strftime("%d.%m.%Y %H:%M")))
    y += lh * 1.4
    this = weeks[-1]
    total_sessions = sum(w["sessions"] for w in weeks)
    total_minutes = sum(w["minutes"] for w in weeks)
    p.setPen(theme.INK)
    lines = [
        tr("Занятий за 8 недель: %1").replace("%1", str(total_sessions)),
        tr("Минут занятий за 8 недель: %1").replace("%1", f"{total_minutes:.0f}"),
        tr("Звёздочек всего: %1").replace("%1", str(db.total_stars())),
        tr("Средняя концентрация на уровне (эта неделя): %1 с").replace("%1", f"{this['avg_focus_s']:.0f}"),
    ]
    for line in lines:
        p.drawText(QRectF(0, y, W, lh), Qt.AlignmentFlag.AlignLeft, line)
        y += lh
    y += lh * 0.5
    ch = W * 0.36
    draw_bar_chart(p, QRectF(0, y, W / 2 - 10, ch), weeks, "minutes", tr("Минут в неделю"), theme.ACCENT, lambda v: f"{v:.0f}")
    draw_bar_chart(p, QRectF(W / 2 + 10, y, W / 2 - 10, ch), weeks, "avg_focus_s",
                   tr("Концентрация на уровне, с"), theme.BLUE, lambda v: f"{v:.0f}")
    y += ch + 20
    draw_errors_chart(p, QRectF(0, y, W, ch), weeks)
    y += ch + 30
    heading(tr("По упражнениям"), 13)
    cols = [tr("Упражнение"), tr("Уровень"), tr("Попыток"), tr("Звёзд"), tr("Имп."), tr("Посл."), tr("Проп."), tr("Реакция, мс")]
    widths = [0.31, 0.09, 0.1, 0.09, 0.08, 0.08, 0.08, 0.17]
    p.setPen(theme.INK_SOFT)

    def row(values, bold=False):
        nonlocal y
        rf = QFont(f)
        rf.setBold(bold)
        p.setFont(rf)
        x = 0.0
        for v, wf in zip(values, widths):
            p.drawText(QRectF(x, y, W * wf, lh), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(v))
            x += W * wf
        y += lh
        p.setPen(QPen(QColor("#E3ECE8"), 1))
        p.drawLine(QPointF(0, y), QPointF(W, y))
        p.setPen(theme.INK)

    row(cols, True)
    for s in db.exercise_stats():
        row([exercise_titles.get(s["exercise"], s["exercise"]), s["level"], s["n"], s["stars"] or 0, s["imp"] or 0,
             s["seq"] or 0, s["om"] or 0, f"{s['rt']:.0f}" if s["rt"] else "—"])
    y += lh
    p.setPen(theme.INK_SOFT)
    p.drawText(QRectF(0, y, W, lh * 3), Qt.TextFlag.TextWordWrap,
               tr("Приложение — вспомогательный инструмент и не заменяет консультацию специалиста.") + "\n"
               + f"{tr(APP_NAME)} {__version__} · {tr(AUTHOR)} · {AUTHOR_SITE}")
    p.end()
