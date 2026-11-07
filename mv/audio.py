from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, QUrl, Signal

from mv.i18n import current_language, tr_voice
from mv.paths import DATA
from mv.phrases import PHRASES

log = logging.getLogger(__name__)

try:
    from PySide6.QtMultimedia import QAudio, QAudioOutput, QMediaPlayer, QSoundEffect

    HAVE_MULTIMEDIA = True
except Exception:  # pragma: no cover - зависит от системы
    HAVE_MULTIMEDIA = False

SFX = ["bell", "pipe", "pop", "soft", "tick", "chime", "whoosh", "step"]


def phrase_text(keys: list[str]) -> str:
    parts = [tr_voice(PHRASES[k]) for k in keys if k in PHRASES]
    text = " ".join(parts).replace(" ,", ",")
    if current_language() == "zh":
        text = text.replace(" ", "")
    return text


class Audio(QObject):
    subtitle = Signal(str)
    finished = Signal()
    speaking = Signal(bool)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._queue: list[str] = []
        self._busy = False
        self._fallback = QTimer(self)
        self._fallback.setSingleShot(True)
        self._fallback.timeout.connect(self._next)
        self._effects: dict[str, object] = {}
        self.player = self.music = None
        if HAVE_MULTIMEDIA:
            try:
                self.out = QAudioOutput(self)
                self.player = QMediaPlayer(self)
                self.player.setAudioOutput(self.out)
                self.player.mediaStatusChanged.connect(self._status)
                self.player.errorOccurred.connect(lambda *_: self._fallback.start(300))
                self.music_out = QAudioOutput(self)
                self.music = QMediaPlayer(self)
                self.music.setAudioOutput(self.music_out)
                self.music.setLoops(QMediaPlayer.Loops.Infinite)
                for name in SFX:
                    path = DATA / "sfx" / f"{name}.wav"
                    if path.exists():
                        e = QSoundEffect(self)
                        e.setSource(QUrl.fromLocalFile(str(path)))
                        self._effects[name] = e
            except Exception:  # pragma: no cover
                log.exception("audio init failed")
                self.player = self.music = None
        self.apply_volume()

    def volume(self) -> float:
        v = max(0, min(int(self.settings.get("volume")), int(self.settings.get("volume_cap")))) / 100.0
        if HAVE_MULTIMEDIA:
            return QAudio.convertVolume(v, QAudio.VolumeScale.LogarithmicVolumeScale, QAudio.VolumeScale.LinearVolumeScale)
        return v

    def apply_volume(self) -> None:
        v = self.volume()
        if self.player:
            self.out.setVolume(v)
            self.music_out.setVolume(v * 0.45)
        for e in self._effects.values():
            e.setVolume(v * 0.8)

    # voice
    def say(self, keys) -> None:
        if isinstance(keys, str):
            keys = [keys]
        self.stop_voice(emit=False)
        self._queue = list(keys)
        self.subtitle.emit(phrase_text(self._queue))
        self._busy = True
        self.speaking.emit(True)
        self._next()

    def stop_voice(self, emit: bool = False) -> None:
        self._queue = []
        self._fallback.stop()
        if self.player:
            self.player.stop()
        if self._busy:
            self._busy = False
            self.speaking.emit(False)
            if emit:
                self.finished.emit()

    @property
    def busy(self) -> bool:
        return self._busy

    def _voice_file(self, key: str):
        for lang in (current_language(), "ru"):
            path = DATA / "voice" / lang / f"{key}.ogg"
            if path.exists():
                return path, lang == current_language()
        return None, False

    def _next(self) -> None:
        if not self._queue:
            if self._busy:
                self._busy = False
                self.speaking.emit(False)
                self.finished.emit()
            return
        key = self._queue.pop(0)
        path, same_lang = self._voice_file(key)
        if self.player and self.settings.get("voice") and path and same_lang:
            self.player.setSource(QUrl.fromLocalFile(str(path)))
            self.player.play()
        else:
            text = tr_voice(PHRASES.get(key, ""))
            self._fallback.start(500 + 55 * len(text))

    def _status(self, status) -> None:
        if status in (QMediaPlayer.MediaStatus.EndOfMedia, QMediaPlayer.MediaStatus.InvalidMedia):
            QTimer.singleShot(120, self._next)

    # effects and music
    def sfx(self, name: str) -> None:
        e = self._effects.get(name)
        if e is not None:
            e.play()

    def play_music(self, name: str = "calm") -> None:
        path = DATA / "sfx" / f"{name}.ogg"
        if self.music and self.settings.get("music") and path.exists():
            self.music.setSource(QUrl.fromLocalFile(str(path)))
            self.music.play()

    def stop_music(self) -> None:
        if self.music:
            self.music.stop()
