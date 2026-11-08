from __future__ import annotations

import ctypes
import logging

from PySide6.QtCore import QObject, QTimer, Signal

log = logging.getLogger(__name__)

BUTTONS = {
    0: "a",  # SDL_CONTROLLER_BUTTON_A
    1: "b",
    2: "x",
    3: "y",
    4: "back",
    6: "start",
    11: "up",
    12: "down",
    13: "left",
    14: "right",
}
REPEATABLE = {"up", "down", "left", "right"}


class Gamepad(QObject):
    """Опрос геймпада через SDL2 (Steam Deck, Xbox, DualShock…) без окна SDL."""

    button = Signal(str)
    stick = Signal(float, float)
    connected = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sdl = None
        self.controllers: dict[int, object] = {}
        self._held: dict[str, int] = {}
        try:
            import sdl2  # noqa: PLC0415

            sdl2.SDL_SetHint(sdl2.SDL_HINT_NO_SIGNAL_HANDLERS, b"1")
            sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")
            if sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER) != 0:
                raise RuntimeError(sdl2.SDL_GetError().decode(errors="replace"))
            self.sdl = sdl2
        except Exception as exc:  # pragma: no cover - зависит от системы
            log.info("gamepad disabled: %s", exc)
            return
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(16)

    @property
    def available(self) -> bool:
        return bool(self.controllers)

    def poll(self) -> None:
        sdl2 = self.sdl
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(ctypes.byref(event)):
            t = event.type
            if t == sdl2.SDL_CONTROLLERDEVICEADDED:
                c = sdl2.SDL_GameControllerOpen(event.cdevice.which)
                if c:
                    jid = sdl2.SDL_JoystickInstanceID(sdl2.SDL_GameControllerGetJoystick(c))
                    self.controllers[jid] = c
                    self.connected.emit(True)
            elif t == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                c = self.controllers.pop(event.cdevice.which, None)
                if c:
                    sdl2.SDL_GameControllerClose(c)
                self.connected.emit(bool(self.controllers))
            elif t == sdl2.SDL_CONTROLLERBUTTONDOWN:
                name = BUTTONS.get(event.cbutton.button)
                if name:
                    self.button.emit(name)
                    if name in REPEATABLE:
                        self._held[name] = -25
            elif t == sdl2.SDL_CONTROLLERBUTTONUP:
                self._held.pop(BUTTONS.get(event.cbutton.button, ""), None)
        for name in list(self._held):
            self._held[name] += 1
            if self._held[name] >= 8:
                self._held[name] = 0
                self.button.emit(name)
        if self.controllers:
            x = y = 0.0
            for c in self.controllers.values():
                for ax, ay in ((0, 1), (2, 3)):
                    vx = sdl2.SDL_GameControllerGetAxis(c, ax) / 32767.0
                    vy = sdl2.SDL_GameControllerGetAxis(c, ay) / 32767.0
                    if abs(vx) > abs(x):
                        x = vx
                    if abs(vy) > abs(y):
                        y = vy
            dead = 0.22
            if abs(x) > dead or abs(y) > dead:
                self.stick.emit(x if abs(x) > dead else 0.0, y if abs(y) > dead else 0.0)
