"""Иконка приложения (голова Тихона): python tools/gen_icon.py → mv/data/icon.png + packaging/icons/"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter  # noqa: E402

from mv import APP_ID, theme  # noqa: E402
from mv.tikhon import _draw_head  # noqa: E402


def render(size: int) -> QImage:
    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size / 512, size / 512)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(theme.ACCENT))
    p.drawRoundedRect(QRectF(16, 16, 480, 480), 110, 110)
    k = 2.9
    p.translate(256 - 100 * k, 270 - 78 * k)
    p.scale(k, k)
    _draw_head(p, "praise", 1.0, False)
    p.end()
    return img


app = QGuiApplication([])
render(512).save(str(ROOT / "mv" / "data" / "icon.png"))
icons = ROOT / "packaging" / "icons"
for s in (48, 64, 128, 256, 512):
    d = icons / f"{s}x{s}"
    d.mkdir(parents=True, exist_ok=True)
    render(s).save(str(d / f"{APP_ID}.png"))
