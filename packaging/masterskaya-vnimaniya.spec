# PyInstaller: pyinstaller --noconfirm packaging/masterskaya-vnimaniya.spec
from pathlib import Path

import sdl2dll

ROOT = Path(SPECPATH).parent
SDL = Path(sdl2dll.__file__).parent / "dll" / "libSDL2-2.0.so"

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT)],
    binaries=[(str(SDL), "sdl2dll/dll")],
    datas=[(str(ROOT / "mv" / "data"), "mv/data"), (str(ROOT / "mv" / "i18n"), "mv/i18n")],
    hiddenimports=["sdl2", "sdl2.dll", "sdl2.gamecontroller", "sdl2dll"],
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQml", "PySide6.QtQuick",
              "PySide6.Qt3DCore", "PySide6.QtPdf", "PySide6.QtVirtualKeyboard", "numpy", "piper", "onnxruntime"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="masterskaya-vnimaniya", console=False, strip=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="masterskaya-vnimaniya")
