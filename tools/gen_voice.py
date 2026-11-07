"""Озвучка фраз Тихона с помощью Piper TTS (офлайн).

python tools/gen_voice.py [--models ~/piper] [--force]
Модели: ru_RU-irina-medium, en_US-amy-medium, zh_CN-huayan-medium
(https://huggingface.co/rhasspy/piper-voices). Результат: mv/data/voice/<lang>/<key>.ogg
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]

from i18n import load  # noqa: E402

from mv.phrases import PHRASES  # noqa: E402

MODELS = {"ru": "ru_RU-irina-medium", "en": "en_US-amy-medium", "zh": "zh_CN-huayan-medium"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=str(Path.home() / "piper"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--lang", nargs="*", default=list(MODELS))
    args = ap.parse_args()

    from piper import PiperVoice, SynthesisConfig

    cfg = SynthesisConfig(length_scale=1.12, noise_scale=0.6, noise_w_scale=0.7)
    for lang in args.lang:
        voice = PiperVoice.load(str(Path(args.models) / f"{MODELS[lang]}.onnx"))
        tr = {} if lang == "ru" else {src: t for (ctx, src), t in load(ROOT / "mv" / "i18n" / f"{lang}.ts").items()
                                      if ctx == "voice"}
        out = ROOT / "mv" / "data" / "voice" / lang
        out.mkdir(parents=True, exist_ok=True)
        for key, text in PHRASES.items():
            target = out / f"{key}.ogg"
            if target.exists() and not args.force:
                continue
            spoken = tr.get(text, text).strip(" ,，:：").replace("«", "").replace("»", "").replace("“", "").replace("”", "")
            with tempfile.TemporaryDirectory() as tmp:
                wav = Path(tmp) / "v.wav"
                with wave.open(str(wav), "wb") as w:
                    voice.synthesize_wav(spoken, w, syn_config=cfg)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                                "-af", "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                                       "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                                       "apad=pad_dur=0.15",
                                "-ac", "1", "-c:a", "libvorbis", "-q:a", "4", str(target)], check=True)
            print(lang, key, spoken)


if __name__ == "__main__":
    main()
