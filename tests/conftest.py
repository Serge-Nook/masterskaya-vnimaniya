import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from PySide6.QtCore import QObject, Signal  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from mv.db import Database  # noqa: E402


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def db(tmp_path):
    d = Database(tmp_path / "t.sqlite3")
    yield d
    d.close()


class FakeAudio(QObject):
    subtitle = Signal(str)
    finished = Signal()
    speaking = Signal(bool)

    def __init__(self):
        super().__init__()
        self.said = []
        self.effects = []

    def say(self, keys):
        self.said.append(keys)

    def stop_voice(self, emit=False):
        pass

    def sfx(self, name):
        self.effects.append(name)

    def play_music(self, name="calm"):
        pass

    def stop_music(self):
        pass

    def apply_volume(self):
        pass


@pytest.fixture
def ctx(app, db):
    return SimpleNamespace(db=db, audio=FakeAudio(), windowed=True)
