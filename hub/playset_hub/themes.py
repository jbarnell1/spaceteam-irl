"""Themes on disk and random clip selection.

themes/
  spaceship/
    theme.json        {"name": "Spaceship", "icon": "🚀"}   (optional)
    select.wav        played when the theme is picked       (optional)
    button-1/  launch.mp3 countdown.mp3
    button-2/  shields.mp3
  _system/
    startup.wav       startup chime                         (optional)
    select.wav        fallback theme-picked sound           (optional)
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".opus"}
SYSTEM_DIR = "_system"


def _audio_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS)


def _first_audio(folder: Path, stem: str) -> Path | None:
    for p in _audio_files(folder):
        if p.stem == stem:
            return p
    return None


@dataclass
class Theme:
    id: str
    name: str
    icon: str
    path: Path
    clips: dict[int, list[Path]] = field(default_factory=dict)

    @property
    def select_sound(self) -> Path | None:
        return _first_audio(self.path, "select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "clip_counts": {str(b): len(c) for b, c in sorted(self.clips.items())},
        }


class ThemeLibrary:
    def __init__(self, root: Path, button_count: int = 5):
        self.root = Path(root)
        self.button_count = button_count
        self.themes: dict[str, Theme] = {}
        self.reload()

    def reload(self) -> None:
        themes: dict[str, Theme] = {}
        if self.root.is_dir():
            for folder in sorted(self.root.iterdir()):
                if not folder.is_dir() or folder.name.startswith(("_", ".")):
                    continue
                themes[folder.name] = self._load_theme(folder)
        self.themes = themes

    def _load_theme(self, folder: Path) -> Theme:
        meta: dict = {}
        meta_file = folder / "theme.json"
        if meta_file.is_file():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                meta = {}
        clips = {b: _audio_files(folder / f"button-{b}") for b in range(1, self.button_count + 1)}
        return Theme(
            id=folder.name,
            name=str(meta.get("name") or folder.name.replace("-", " ").title()),
            icon=str(meta.get("icon") or ""),
            path=folder,
            clips=clips,
        )

    def get(self, theme_id: str | None) -> Theme | None:
        return self.themes.get(theme_id) if theme_id else None

    def system_sound(self, stem: str) -> Path | None:
        return _first_audio(self.root / SYSTEM_DIR, stem)


class ClipPicker:
    """Random clip per press, never the same clip twice in a row for one button."""

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()
        self._last: dict[tuple[str, int], Path] = {}

    def pick(self, theme: Theme, button: int) -> Path | None:
        clips = theme.clips.get(button) or []
        if not clips:
            return None
        key = (theme.id, button)
        last = self._last.get(key)
        choices = [c for c in clips if c != last] or clips
        clip = self._rng.choice(choices)
        self._last[key] = clip
        return clip
