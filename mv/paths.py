import os
from pathlib import Path

from mv import APP_ID

PKG_DIR = Path(__file__).resolve().parent
DATA = PKG_DIR / "data"
I18N = PKG_DIR / "i18n"


def user_data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    path = Path(base) / APP_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def documents_dir() -> Path:
    for candidate in (os.environ.get("XDG_DOCUMENTS_DIR"), "~/Documents", "~/Документы", "~"):
        if candidate:
            p = Path(os.path.expanduser(candidate))
            if p.is_dir():
                return p
    return Path.home()
