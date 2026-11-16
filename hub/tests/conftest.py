from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path

import pytest

from playset_hub.config import Config
from playset_hub.hub import Hub
from playset_hub.player import RecordingPlayer
from playset_hub.themes import ClipPicker, ThemeLibrary


def make_themes(root: Path) -> Path:
    def touch(p: Path) -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"RIFF")

    (root / "spaceship").mkdir(parents=True)
    (root / "spaceship" / "theme.json").write_text(json.dumps({"name": "Spaceship", "icon": "🚀"}), encoding="utf-8")
    touch(root / "spaceship" / "button-1" / "launch.mp3")
    touch(root / "spaceship" / "button-1" / "countdown.mp3")
    touch(root / "spaceship" / "button-2" / "shields.wav")
    touch(root / "spaceship" / "select.wav")
    touch(root / "pirate-ship" / "button-1" / "arr.ogg")
    touch(root / "pirate-ship" / "button-1" / "notes.txt")  # not audio, ignored
    touch(root / "_system" / "startup.wav")
    touch(root / "_system" / "select.wav")
    return root


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def themes_dir(tmp_path: Path) -> Path:
    return make_themes(tmp_path / "themes")


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def make_hub(tmp_path: Path, themes_dir: Path, clock: FakeClock):
    def _make(now: datetime | None = None, **config_overrides) -> Hub:
        config = Config(**config_overrides)
        return Hub(
            config,
            ThemeLibrary(themes_dir),
            RecordingPlayer(),
            state_path=tmp_path / "data" / "state.json",
            press_log_path=tmp_path / "data" / "presses.csv",
            picker=ClipPicker(random.Random(1)),
            clock=clock,
            now=(lambda: now) if now else datetime.now,
        )

    return _make
