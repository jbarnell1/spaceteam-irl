"""Hub core: takes button events, applies dedupe and quiet hours, hands presses to the active mode."""

from __future__ import annotations

import csv
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import PLAY_MODES, Config, QuietHours, State
from .events import ButtonEvent, Deduper
from .modes import FreePlayMode, Mode
from .player import Player
from .themes import ClipPicker, ThemeLibrary

log = logging.getLogger(__name__)


@dataclass
class ButtonStatus:
    id: int
    battery_mv: int = 0
    last_press: float | None = None
    rssi: int = 0
    presses: int = 0


class Hub:
    def __init__(
        self,
        config: Config,
        library: ThemeLibrary,
        player: Player,
        state_path: Path,
        press_log_path: Path | None = None,
        picker: ClipPicker | None = None,
        clock=time.monotonic,
        now=datetime.now,
    ):
        self.config = config
        self.library = library
        self.player = player
        self.state_path = Path(state_path)
        self.press_log_path = Path(press_log_path) if press_log_path else None
        self.picker = picker or ClipPicker()
        self.deduper = Deduper(config.dedupe_window_s, clock=clock)
        self._now = now
        self.state = State.load(self.state_path)
        self.mode: Mode = FreePlayMode()
        self.buttons = {int(b["id"]): ButtonStatus(int(b["id"])) for b in config.buttons}
        if self.library.get(self.state.active_theme) is None:
            self.state.active_theme = next(iter(self.library.themes), None)

    # ── Volume and quiet hours ───────────────────────────────────────
    @property
    def effective_volume(self) -> int:
        return max(0, min(self.state.volume, self.config.max_volume))

    def is_quiet(self) -> bool:
        return self.state.quiet_hours.active_at(self._now().time())

    async def _play(self, path: Path | None, *, interrupt: bool | None = None, force: bool = False) -> bool:
        if path is None:
            return False
        if self.is_quiet() and not force:
            return False
        if interrupt is None:
            interrupt = self.state.play_mode == "interrupt"
        await self.player.play(path, self.effective_volume, interrupt)
        return True

    # ── Events ───────────────────────────────────────────────────────
    async def handle_event(self, event: ButtonEvent) -> bool:
        """Returns True if the event was accepted (not a duplicate)."""
        if self.deduper.is_duplicate(event):
            log.debug("dropped duplicate button=%d seq=%d", event.button, event.seq)
            return False
        status = self.buttons.setdefault(event.button, ButtonStatus(event.button))
        status.last_press = event.received_at
        status.rssi = event.rssi
        status.presses += 1
        if event.battery_mv:
            status.battery_mv = event.battery_mv
        self._log_press(event)
        if self.is_battery_low(status):
            log.warning("button %d battery low: %d mV", event.button, status.battery_mv)
        await self.mode.on_press(self, event)
        return True

    def is_battery_low(self, status: ButtonStatus) -> bool:
        return 0 < status.battery_mv < self.config.low_battery_mv

    def _log_press(self, event: ButtonEvent) -> None:
        if not self.press_log_path:
            return
        new_file = not self.press_log_path.exists()
        self.press_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.press_log_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["time", "button", "seq", "event", "battery_mv", "rssi"])
            writer.writerow([
                datetime.fromtimestamp(event.received_at).isoformat(timespec="seconds"),
                event.button, event.seq, event.event, event.battery_mv, event.rssi,
            ])

    # ── Actions used by modes and the web UI ─────────────────────────
    async def play_button_clip(self, button: int, *, force: bool = False) -> Path | None:
        theme = self.library.get(self.state.active_theme)
        if theme is None:
            return None
        clip = self.picker.pick(theme, button)
        played = await self._play(clip, force=force)
        return clip if played else None

    async def startup(self) -> None:
        await self._play(self.library.system_sound("startup"), interrupt=True)

    async def set_theme(self, theme_id: str) -> bool:
        theme = self.library.get(theme_id)
        if theme is None:
            return False
        self.state.active_theme = theme_id
        self.state.save(self.state_path)
        sound = theme.select_sound or self.library.system_sound("select")
        # The parent is holding the phone and just asked for this: play it even in quiet hours.
        await self._play(sound, interrupt=True, force=True)
        return True

    def update_settings(self, data: dict) -> None:
        """Applies all changes or none. Raises ValueError/TypeError on bad input."""
        volume = self.state.volume
        if "volume" in data:
            volume = max(0, min(100, int(data["volume"])))
        quiet = self.state.quiet_hours
        if isinstance(data.get("quiet_hours"), dict):
            qh = data["quiet_hours"]
            quiet = QuietHours(
                enabled=bool(qh.get("enabled", quiet.enabled)),
                start=str(qh.get("start", quiet.start)),
                end=str(qh.get("end", quiet.end)),
            )
            quiet.validate()
        self.state.volume = volume
        self.state.quiet_hours = quiet
        if data.get("play_mode") in PLAY_MODES:
            self.state.play_mode = data["play_mode"]
        self.state.save(self.state_path)

    def reload_themes(self) -> None:
        self.library.reload()
        if self.library.get(self.state.active_theme) is None:
            self.state.active_theme = next(iter(self.library.themes), None)

    # ── Snapshot for the phone UI ────────────────────────────────────
    def snapshot(self) -> dict:
        buttons = []
        for b in self.config.buttons:
            status = self.buttons.get(int(b["id"]), ButtonStatus(int(b["id"])))
            buttons.append({
                "id": status.id,
                "name": b.get("name"),
                "color": b.get("color"),
                "battery_mv": status.battery_mv or None,
                "battery_low": self.is_battery_low(status),
                "last_press": status.last_press,
                "presses": status.presses,
            })
        return {
            "themes": [t.to_dict() for t in self.library.themes.values()],
            "active_theme": self.state.active_theme,
            "buttons": buttons,
            "mode": {"id": self.mode.id, "name": self.mode.name},
            "quiet_now": self.is_quiet(),
            "settings": {
                "volume": self.state.volume,
                "max_volume": self.config.max_volume,
                "play_mode": self.state.play_mode,
                "quiet_hours": {
                    "enabled": self.state.quiet_hours.enabled,
                    "start": self.state.quiet_hours.start,
                    "end": self.state.quiet_hours.end,
                },
            },
        }
