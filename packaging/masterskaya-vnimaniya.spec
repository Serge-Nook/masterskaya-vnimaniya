# PyInstaller: pyinstaller --noconfirm packaging/masterskaya-vnimaniya.spec
from pathlib import Path

import sdl2dll

ROOT = Path(SPECPATH).parent
SDL_DIR = Path(sdl2dll.__file__).parent / "dll"
SDL_LIBS = ["libSDL2-2.0.so", "libSDL2_mixer-2.0.so", "libogg.so.0", "libopus.so.0", "libopusfile.so.0",
            "libgme.so.0", "libxmp.so.4", "libwavpack.so.1"]

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT)],
    binaries=[(str(SDL_DIR / n), "sdl2dll/dll") for n in SDL_LIBS if (SDL_DIR / n).exists()],
    datas=[(str(ROOT / "mv" / "data"), "mv/data"), (str(ROOT / "mv" / "i18n"), "mv/i18n")],
    hiddenimports=["sdl2", "sdl2.dll", "sdl2.gamecontroller", "sdl2.sdlmixer", "sdl2dll"],
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQml", "PySide6.QtQuick",
              "PySide6.Qt3DCore", "PySide6.QtPdf", "PySide6.QtVirtualKeyboard", "numpy", "piper", "onnxruntime"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="masterskaya-vnimaniya", console=False, strip=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="masterskaya-vnimaniya")
