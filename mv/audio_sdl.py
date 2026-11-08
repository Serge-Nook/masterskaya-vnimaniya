"""Вывод звука через SDL2_mixer: сам выбирает PipeWire/PulseAudio/ALSA системы (SteamOS и др.)."""
from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

VOICE_CHANNEL = 0


class SdlMixer:
    def __init__(self):
        if os.environ.get("MV_AUDIO", "").lower() == "qt":
            raise RuntimeError("disabled by MV_AUDIO=qt")
        import sdl2  # noqa: PLC0415
        from sdl2 import sdlmixer  # noqa: PLC0415

        self.sdl, self.mix = sdl2, sdlmixer
        sdl2.SDL_SetHint(sdl2.SDL_HINT_NO_SIGNAL_HANDLERS, b"1")
        sdl2.SDL_SetHint(b"SDL_APP_NAME", b"Masterskaya vnimaniya")
        if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_AUDIO) != 0:
            raise RuntimeError(self._error())
        sdlmixer.Mix_Init(sdlmixer.MIX_INIT_OGG)
        if sdlmixer.Mix_OpenAudio(44100, sdl2.AUDIO_S16SYS, 2, 1024) != 0:
            err = self._error()
            sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_AUDIO)
            raise RuntimeError(err)
        sdlmixer.Mix_AllocateChannels(12)
        sdlmixer.Mix_ReserveChannels(1)
        self._chunks: dict[str, object] = {}
        self._music = None
        self._music_path = None
        log.info("audio: SDL %s", sdl2.SDL_GetCurrentAudioDriver().decode(errors="replace"))

    def _error(self) -> str:
        return self.sdl.SDL_GetError().decode(errors="replace")

    def _chunk(self, path) -> object | None:
        key = str(path)
        if key not in self._chunks:
            chunk = self.mix.Mix_LoadWAV(key.encode())
            if not chunk:
                log.warning("audio: cannot load %s: %s", path, self._error())
            self._chunks[key] = chunk or None
        return self._chunks[key]

    def play_voice(self, path, volume: float) -> bool:
        chunk = self._chunk(path)
        if chunk is None:
            return False
        self.mix.Mix_Volume(VOICE_CHANNEL, int(volume * 128))
        return self.mix.Mix_PlayChannel(VOICE_CHANNEL, chunk, 0) != -1

    def voice_playing(self) -> bool:
        return bool(self.mix.Mix_Playing(VOICE_CHANNEL))

    def stop_voice(self) -> None:
        self.mix.Mix_HaltChannel(VOICE_CHANNEL)

    def play_effect(self, path, volume: float) -> None:
        chunk = self._chunk(path)
        if chunk is not None:
            ch = self.mix.Mix_PlayChannel(-1, chunk, 0)
            if ch != -1:
                self.mix.Mix_Volume(ch, int(volume * 128))

    def play_music(self, path, volume: float) -> None:
        if self._music_path != str(path):
            if self._music:
                self.mix.Mix_FreeMusic(self._music)
            self._music = self.mix.Mix_LoadMUS(str(path).encode()) or None
            self._music_path = str(path)
        if self._music:
            self.mix.Mix_VolumeMusic(int(volume * 128))
            self.mix.Mix_PlayMusic(self._music, -1)

    def set_music_volume(self, volume: float) -> None:
        self.mix.Mix_VolumeMusic(int(volume * 128))

    def stop_music(self) -> None:
        self.mix.Mix_HaltMusic()

    def close(self) -> None:
        self.mix.Mix_HaltChannel(-1)
        self.mix.Mix_HaltMusic()
        self.mix.Mix_CloseAudio()
