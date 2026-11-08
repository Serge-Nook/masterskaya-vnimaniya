from PySide6.QtGui import QColor

BG = QColor("#EAF3EF")
BG_DEEP = QColor("#D7E8E1")
PANEL = QColor("#FBFAF5")
INK = QColor("#23343B")
INK_SOFT = QColor("#4F6169")
ACCENT = QColor("#5E8C74")
ACCENT_LIGHT = QColor("#A9CBB7")
SAND = QColor("#F3E3C3")
SKY = QColor("#CFE6F2")
GRASS = QColor("#B9D9A6")
FOCUS = QColor("#E0A035")
STAR = QColor("#F2C14E")

RED = QColor("#D7443E")
ORANGE = QColor("#EE9A4D")
YELLOW = QColor("#F2CF5B")
GREEN = QColor("#6DB36D")
BLUE = QColor("#4F8FD0")
PURPLE = QColor("#8E6BBF")
PINK = QColor("#E88FB0")
BROWN = QColor("#9C6B43")
GREY = QColor("#8C979C")

PALETTE = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, BROWN]
RAINBOW = [RED, ORANGE, YELLOW, GREEN, QColor("#5BB5D9"), BLUE, PURPLE]

MIN_TOUCH = 64

STYLESHEET = """
QWidget { color: #23343B; font-family: "Nunito", "Noto Sans SC", "Noto Sans CJK SC", sans-serif; font-size: 20px; }
QMainWindow, #Root { background: #EAF3EF; }
QLabel#Title { font-size: 40px; font-weight: 800; }
QLabel#Subtitle { font-size: 26px; font-weight: 600; color: #4F6169; }
QPushButton { background: #FBFAF5; border: 3px solid #A9CBB7; border-radius: 18px;
  padding: 10px 22px; min-height: 52px; min-width: 64px; font-size: 24px; font-weight: 700; }
QPushButton:hover { background: #F4F8F1; }
QPushButton:pressed { background: #DCEBE2; }
QPushButton:focus { border: 4px solid #E0A035; }
QPushButton:disabled { color: #9AA6AA; border-color: #D5DEDA; }
QPushButton#Primary { background: #5E8C74; color: white; border-color: #5E8C74; }
QPushButton#Primary:focus { border: 4px solid #E0A035; }
QPushButton#Primary:pressed { background: #4B7560; }
QTabWidget::pane { border: 2px solid #A9CBB7; border-radius: 12px; background: #FBFAF5; }
QTabWidget > QStackedWidget > QWidget, QScrollArea > QWidget > QWidget { background: #FBFAF5; }
QTabBar::tab { background: #D7E8E1; padding: 12px 24px; border-top-left-radius: 12px;
  border-top-right-radius: 12px; margin-right: 4px; min-height: 40px; }
QTabBar::tab:selected { background: #FBFAF5; font-weight: 800; }
QSpinBox, QComboBox, QLineEdit { background: white; border: 2px solid #A9CBB7; border-radius: 10px;
  padding: 6px 10px; min-height: 44px; font-size: 22px; }
QSpinBox::up-button, QSpinBox::down-button { width: 36px; }
QCheckBox { spacing: 12px; min-height: 44px; }
QCheckBox::indicator { width: 32px; height: 32px; }
QSlider::groove:horizontal { height: 12px; background: #D7E8E1; border-radius: 6px; }
QSlider::handle:horizontal { width: 40px; height: 40px; margin: -14px 0; border-radius: 20px; background: #5E8C74; }
QTableWidget { background: white; gridline-color: #D7E8E1; font-size: 18px; }
QHeaderView::section { background: #D7E8E1; padding: 6px; border: none; font-weight: 700; font-size: 18px; }
QScrollArea { border: none; background: transparent; }
"""


def apply(app) -> None:
    """Светлая тема независимо от системной (тёмные KDE/Breeze, SteamOS)."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QStyleFactory

    app.setStyle(QStyleFactory.create("Fusion"))
    hints = app.styleHints()
    if hasattr(hints, "setColorScheme"):
        hints.setColorScheme(Qt.ColorScheme.Light)
    pal = QPalette()
    roles = {
        QPalette.ColorRole.Window: BG, QPalette.ColorRole.WindowText: INK,
        QPalette.ColorRole.Base: QColor("white"), QPalette.ColorRole.AlternateBase: BG,
        QPalette.ColorRole.Text: INK, QPalette.ColorRole.PlaceholderText: INK_SOFT,
        QPalette.ColorRole.Button: PANEL, QPalette.ColorRole.ButtonText: INK,
        QPalette.ColorRole.ToolTipBase: PANEL, QPalette.ColorRole.ToolTipText: INK,
        QPalette.ColorRole.Highlight: ACCENT, QPalette.ColorRole.HighlightedText: QColor("white"),
        QPalette.ColorRole.Link: ACCENT, QPalette.ColorRole.BrightText: QColor("white"),
        QPalette.ColorRole.Light: QColor("white"), QPalette.ColorRole.Midlight: BG,
        QPalette.ColorRole.Mid: ACCENT_LIGHT, QPalette.ColorRole.Dark: INK_SOFT, QPalette.ColorRole.Shadow: INK,
    }
    for role, color in roles.items():
        pal.setColor(role, color)
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        pal.setColor(QPalette.ColorGroup.Disabled, role, QColor("#9AA6AA"))
    app.setPalette(pal)
