"""Hub settings.

Two files:
  config.json  hand-edited. Volume ceiling, buttons, player command, network.
               The phone UI can never change these.
  state.json   written by the hub. Active theme and the settings the phone UI can change.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import time as dtime
from pathlib import Path

DEFAULT_BUTTONS = [
    {"id": 1, "name": "Red", "color": "#e5484d"},
    {"id": 2, "name": "Blue", "color": "#3e63dd"},
    {"id": 3, "name": "Green", "color": "#30a46c"},
    {"id": 4, "name": "Yellow", "color": "#f5d90a"},
    {"id": 5, "name": "Purple", "color": "#8e4ec6"},
]

# One mpv process per clip. {volume} is 0-100, {path} the clip file.
DEFAULT_PLAYER_CMD = ["mpv", "--no-video", "--really-quiet", "--volume={volume}", "{path}"]

PLAY_MODES = ("interrupt", "queue")


@dataclass
class Config:
    max_volume: int = 70
    buttons: list[dict] = field(default_factory=lambda: [dict(b) for b in DEFAULT_BUTTONS])
    player_cmd: list[str] = field(default_factory=lambda: list(DEFAULT_PLAYER_CMD))
    low_battery_mv: int = 3500
    dedupe_window_s: float = 2.0
    queue_limit: int = 3
    host: str = "0.0.0.0"
    port: int = 8080

    @classmethod
    def load(cls, path: Path | None) -> "Config":
        cfg = cls()
        if path and Path(path).is_file():
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            for key, value in data.items():
                if hasattr(cfg, key):
                    setattr(cfg, key, value)
        cfg.max_volume = max(0, min(100, int(cfg.max_volume)))
        return cfg

    def button(self, button_id: int) -> dict:
        for b in self.buttons:
            if int(b["id"]) == button_id:
                return b
        return {"id": button_id, "name": f"Button {button_id}", "color": "#888888"}


@dataclass
class QuietHours:
    enabled: bool = False
    start: str = "19:30"  # HH:MM, local time
    end: str = "07:00"

    def validate(self) -> None:
        """Raises ValueError unless start and end are HH:MM."""
        _parse_hhmm(self.start)
        _parse_hhmm(self.end)

    def active_at(self, now: dtime) -> bool:
        if not self.enabled:
            return False
        start, end = _parse_hhmm(self.start), _parse_hhmm(self.end)
        if start == end:
            return False
        if start < end:
            return start <= now < end
        return now >= start or now < end  # window crosses midnight


def _parse_hhmm(value: str) -> dtime:
    hours, minutes = value.split(":")
    return dtime(int(hours), int(minutes))


@dataclass
class State:
    active_theme: str | None = None
    volume: int = 50
    play_mode: str = "interrupt"
    quiet_hours: QuietHours = field(default_factory=QuietHours)

    @classmethod
    def load(cls, path: Path) -> "State":
        state = cls()
        if Path(path).is_file():
            try:
                data = json.loads(Path(path).read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return state
            state.active_theme = data.get("active_theme")
            state.volume = int(data.get("volume", state.volume))
            if data.get("play_mode") in PLAY_MODES:
                state.play_mode = data["play_mode"]
            qh = data.get("quiet_hours") or {}
            state.quiet_hours = QuietHours(
                enabled=bool(qh.get("enabled", False)),
                start=str(qh.get("start", "19:30")),
                end=str(qh.get("end", "07:00")),
            )
        return state

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        os.replace(tmp, path)
