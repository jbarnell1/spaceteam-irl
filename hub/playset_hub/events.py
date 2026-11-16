"""Button events: parsing dongle lines and dropping duplicate retries."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

PROTOCOL_VERSION = 1
EVENT_PRESS = 1


@dataclass(frozen=True)
class ButtonEvent:
    button: int
    seq: int
    event: int = EVENT_PRESS
    battery_mv: int = 0
    rssi: int = 0
    received_at: float = field(default_factory=time.time)


def parse_line(line: str) -> ButtonEvent | None:
    """Parse one dongle JSON line. Returns None for anything that isn't a valid press."""
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(msg, dict) or msg.get("t") != "btn":
        return None
    if msg.get("v") != PROTOCOL_VERSION:
        return None
    try:
        return ButtonEvent(
            button=int(msg["b"]),
            seq=int(msg["seq"]),
            event=int(msg.get("e", EVENT_PRESS)),
            battery_mv=int(msg.get("mv", 0)),
            rssi=int(msg.get("rssi", 0)),
        )
    except (KeyError, TypeError, ValueError):
        return None


class Deduper:
    """Drops an event whose (button, seq) was already seen within `window_s`.

    A time window rather than "seq must increase" so a button that cold-boots
    (and restarts its counter) is never silenced.
    """

    def __init__(self, window_s: float = 2.0, clock=time.monotonic):
        self.window_s = window_s
        self._clock = clock
        self._seen: dict[tuple[int, int], float] = {}

    def is_duplicate(self, event: ButtonEvent) -> bool:
        now = self._clock()
        cutoff = now - self.window_s
        self._seen = {k: t for k, t in self._seen.items() if t >= cutoff}
        key = (event.button, event.seq)
        if key in self._seen:
            return True
        self._seen[key] = now
        return False
