from __future__ import annotations

import argparse
import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler
from types import SimpleNamespace

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication, QIcon, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QAbstractButton, QApplication, QMainWindow, QStackedWidget, QWidget

from mv import APP_ID, APP_NAME, __version__, theme
from mv.audio import DATA, Audio
from mv.db import Database
from mv.exercises.base import Exercise
from mv.gamepad import Gamepad
from mv.i18n import detect_language, install_language, tr
from mv.paths import user_data_dir
from mv.session import Session
from mv.widgets import Pointer

log = logging.getLogger("mv")


class MainWindow(QMainWindow):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        ctx.window = self
        self.setWindowTitle(tr(APP_NAME))
        self.setObjectName("Root")
        self.setMinimumSize(1024, 640)
        self.stack = QStackedWidget()
        self.stack.setObjectName("Root")
        self.setCentralWidget(self.stack)
        self.pointer = Pointer(self)
        self.screens: dict[str, QWidget] = {}
        self.current: QWidget | None = None
        self.return_to: str | None = None
        ctx.session.time_up.connect(self._time_up)
        ctx.gamepad.button.connect(self._pad_button)
        ctx.gamepad.stick.connect(self._pad_stick)
        self.pointer_hide = QTimer(self)
        self.pointer_hide.setSingleShot(True)
        self.pointer_hide.timeout.connect(self.pointer.hide)

    # навигация
    def _screen(self, name: str, factory):
        if name not in self.screens:
            w = factory()
            w.setObjectName("Root")
            self.screens[name] = w
            self.stack.addWidget(w)
        return self.screens[name]

    def show_screen(self, name: str, factory, **attrs):
        w = self._screen(name, factory)
        for k, v in attrs.items():
            setattr(w, k, v)
        if self.current is not None and self.current is not w:
            try:
                self.current.on_leave()
            except Exception:
                log.exception("on_leave failed")
        self.current = w
        self.current_name = name
        self.stack.setCurrentWidget(w)
        w.on_enter()
        f = w.first_focus()
        if f is not None:
            f.setFocus()
        return w

    def start(self):
        if not self.ctx.db.get("disclaimer_accepted"):
            from mv.screens.child import DisclaimerScreen

            self.show_screen("disclaimer", lambda: DisclaimerScreen(self.ctx))
        else:
            self.go_home(greet=True)

    def _gate(self) -> bool:
        """Перерыв и дневной лимит — до любого игрового экрана."""
        if self.ctx.db.pending_break() > 0:
            self.open_break()
            return False
        if self.ctx.session.daily_limit_reached() and not self.ctx.session.running:
            from mv.screens.child import DayDoneScreen

            self.show_screen("daydone", lambda: DayDoneScreen(self.ctx))
            return False
        return True

    def go_home(self, greet: bool = False, key: str | None = None):
        if not self._gate():
            return
        from mv.screens.child import HomeScreen

        self.show_screen("home", lambda: HomeScreen(self.ctx),
                         greet_key=key or ("hello" if greet and self.ctx.db.total_stars() == 0 else "hello_again"))

    def open_workshop(self, key: str):
        if self.ctx.session.expired:
            self.start_break()
            return
        if not self._gate():
            return
        from mv.screens.child import WorkshopScreen

        self.show_screen(f"ws:{key}", lambda: WorkshopScreen(self.ctx, key))

    def start_exercise(self, cls):
        if not self._gate():
            return
        from mv.screens.child import ExerciseHost

        self.show_screen(f"ex:{cls.key}", lambda: ExerciseHost(self.ctx, cls))

    def open_garden(self):
        from mv.screens.child import GardenScreen

        self.show_screen("garden", lambda: GardenScreen(self.ctx))

    def _time_up(self):
        name = getattr(self, "current_name", "")
        if not name.startswith("ex:"):
            self.start_break()
        elif self.current.mode != "play":
            self.start_break()

    def start_break(self):
        self.ctx.session.end()
        self.ctx.db.start_break(int(self.ctx.db.get("break_minutes")) * 60)
        self.open_break()

    def open_break(self):
        from mv.screens.child import BreakScreen

        self.ctx.session.end()
        self.show_screen("break", lambda: BreakScreen(self.ctx))

    def after_break(self):
        self.go_home(key="break_done")

    def open_adult(self):
        from mv.screens.adult import PinScreen

        self.ctx.audio.stop_voice()
        self.ctx.session.pause(True)
        if getattr(self, "current_name", "") not in ("pin", "adult"):
            self.return_to = getattr(self, "current_name", None)
        self.show_screen("pin", lambda: PinScreen(self.ctx))

    def show_adult_panel(self):
        from mv.screens.adult import AdultScreen

        self.show_screen("adult", lambda: AdultScreen(self.ctx))

    def leave_adult(self):
        self.ctx.session.pause(False)
        self.ctx.audio.apply_volume()
        back = self.return_to
        self.return_to = None
        if back and back.startswith("ex:") and back in self.screens and self._gate():
            self.show_screen(back, lambda: None)
        elif back and back.startswith("ws:") and back in self.screens:
            self.open_workshop(back[3:])
        elif back == "disclaimer":
            self.start()
        else:
            self.go_home()

    def reload_language(self):
        install_language(self.ctx.db.get("language") or detect_language())
        self.setWindowTitle(tr(APP_NAME))
        for w in self.screens.values():
            self.stack.removeWidget(w)
            w.deleteLater()
        self.screens.clear()
        self.current = None
        self.show_adult_panel()
        self.return_to = None

    def apply_fullscreen(self):
        if self.ctx.db.get("fullscreen") and not self.ctx.windowed:
            self.showFullScreen()
        else:
            self.showNormal()

    def quit_app(self):
        self.ctx.session.end()
        self.ctx.audio.stop_music()
        self.close()

    def closeEvent(self, e):
        self.ctx.session.end()
        super().closeEvent(e)

    # клавиатура и геймпад
    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Back):
            self.current.back()
            return
        super().keyPressEvent(e)

    def _pad_button(self, name: str):
        if not self.isActiveWindow() and not self.ctx.windowed:
            return
        focus = QApplication.focusWidget()
        if name == "b":
            self.current.back()
        elif name == "a":
            if self.pointer.isVisible():
                self._pointer_click()
            elif isinstance(focus, QAbstractButton):
                focus.animateClick()
            elif isinstance(focus, Exercise):
                self._send_key(focus, Qt.Key.Key_Return)
        elif name in ("up", "down", "left", "right"):
            self.pointer.hide()
            if isinstance(focus, Exercise):
                key = {"up": Qt.Key.Key_Up, "down": Qt.Key.Key_Down, "left": Qt.Key.Key_Left, "right": Qt.Key.Key_Right}[name]
                self._send_key(focus, key)
            else:
                self._move_focus(name)

    def _send_key(self, w, key):
        QApplication.sendEvent(w, QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier))
        QApplication.sendEvent(w, QKeyEvent(QEvent.Type.KeyRelease, key, Qt.KeyboardModifier.NoModifier))

    def _move_focus(self, direction: str):
        candidates = [b for b in self.current.findChildren(QAbstractButton)
                      if b.isVisible() and b.isEnabled() and b.focusPolicy() != Qt.FocusPolicy.NoFocus]
        if not candidates:
            return
        focus = QApplication.focusWidget()
        if focus not in candidates:
            candidates[0].setFocus()
            return
        c0 = focus.mapTo(self, focus.rect().center())
        best, best_score = None, None
        for b in candidates:
            if b is focus:
                continue
            c = b.mapTo(self, b.rect().center())
            dx, dy = c.x() - c0.x(), c.y() - c0.y()
            main, side = {"left": (-dx, dy), "right": (dx, dy), "up": (-dy, dx), "down": (dy, dx)}[direction]
            if main <= 4:
                continue
            score = main + abs(side) * 2.5
            if best_score is None or score < best_score:
                best, best_score = b, score
        if best is not None:
            best.setFocus(Qt.FocusReason.TabFocusReason)

    def _pad_stick(self, x: float, y: float):
        if not self.pointer.isVisible():
            self.pointer.setGeometry(self.rect())
            c = QApplication.focusWidget()
            start = c.mapTo(self, c.rect().center()) if c is not None and self.isAncestorOf(c) else self.rect().center()
            self.pointer.pos_f = QPointF(start)
            self.pointer.show()
            self.pointer.raise_()
        speed = 16
        p = self.pointer.pos_f
        self.pointer.pos_f = QPointF(max(0, min(self.width(), p.x() + x * speed)), max(0, min(self.height(), p.y() + y * speed)))
        self.pointer.update()
        self.pointer_hide.start(6000)
        w = self.childAt(self.pointer.pos_f.toPoint())
        if isinstance(w, Exercise) or (w is not None and isinstance(w.parentWidget(), Exercise)):
            target = w if isinstance(w, Exercise) else w.parentWidget()
            local = target.mapFrom(self, self.pointer.pos_f.toPoint())
            QApplication.sendEvent(target, QMouseEvent(QEvent.Type.MouseMove, QPointF(local), QPointF(local),
                                                       Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier))

    def _pointer_click(self):
        pt = self.pointer.pos_f.toPoint()
        self.pointer.hide()
        w = self.childAt(pt)
        self.pointer.show()
        if w is None:
            return
        local = QPointF(w.mapFrom(self, pt))
        glob = QPointF(self.mapToGlobal(pt))
        for t, buttons in ((QEvent.Type.MouseButtonPress, Qt.MouseButton.LeftButton),
                           (QEvent.Type.MouseButtonRelease, Qt.MouseButton.NoButton)):
            QApplication.sendEvent(w, QMouseEvent(t, local, glob, Qt.MouseButton.LeftButton, buttons, Qt.KeyboardModifier.NoModifier))
        self.pointer_hide.start(6000)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.pointer.setGeometry(self.rect())

    def handle_crash(self):
        """Падение одной игры не роняет приложение — возвращаемся к выбору."""
        cur = self.current
        if cur is not None and hasattr(cur, "abort"):
            try:
                cur.abort()
                return
            except Exception:
                log.exception("abort failed")
        try:
            self.go_home()
        except Exception:
            log.exception("go_home failed")


def setup_logging() -> None:
    path = user_data_dir() / "app.log"
    handler = RotatingFileHandler(path, maxBytes=512_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler, logging.StreamHandler()])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=APP_ID)
    parser.add_argument("--windowed", action="store_true", help="не разворачивать на весь экран")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--lang", choices=["ru", "en", "zh"])
    args, qt_args = parser.parse_known_args(argv if argv is not None else sys.argv[1:])

    setup_logging()
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication([sys.argv[0], *qt_args])
    app.setApplicationName(APP_ID)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setDesktopFileName(APP_ID)
    icon = DATA / "icon.png"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    for font in (DATA / "fonts").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font))
    QFont.insertSubstitution("Nunito", "Noto Sans SC")
    app.setStyleSheet(theme.STYLESHEET)

    db = Database(user_data_dir() / "data.sqlite3")
    lang = args.lang or db.get("language") or detect_language()
    install_language(lang)
    app.setApplicationDisplayName(tr(APP_NAME))
    ctx = SimpleNamespace(db=db, windowed=args.windowed)
    ctx.audio = Audio(db)
    ctx.gamepad = Gamepad()
    ctx.session = Session(db)
    window = MainWindow(ctx)

    def excepthook(exc_type, exc, tb):
        log.error("unhandled: %s", "".join(traceback.format_exception(exc_type, exc, tb)))
        QTimer.singleShot(0, window.handle_crash)

    sys.excepthook = excepthook
    window.resize(1280, 800)
    window.apply_fullscreen()
    if not window.isVisible():
        window.show()
    window.start()
    code = app.exec()
    ctx.session.end()
    db.close()
    return code
