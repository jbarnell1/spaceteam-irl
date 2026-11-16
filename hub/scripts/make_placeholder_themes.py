"""Generate placeholder beep themes so the hub has something to play before real recordings exist.

    uv run python scripts/make_placeholder_themes.py themes

Creates spaceship/ and pirate-ship/ with two synth clips per button, a select
sound per theme, and _system/startup.wav. Existing files are left alone.
Standard library only.
"""

from __future__ import annotations

import json
import math
import struct
import sys
import wave
from pathlib import Path

RATE = 22050


def tone(freqs: list[tuple[float, float, float]], volume: float = 0.5) -> bytes:
    """freqs: (start_hz, end_hz, seconds) segments, each a sine sweep with a short fade."""
    frames = bytearray()
    phase = 0.0
    for start, end, secs in freqs:
        n = int(RATE * secs)
        fade = min(int(RATE * 0.01), n // 2)
        for i in range(n):
            f = start + (end - start) * i / max(1, n - 1)
            phase += 2 * math.pi * f / RATE
            env = min(1.0, i / fade if fade else 1, (n - 1 - i) / fade if fade else 1)
            frames += struct.pack("<h", int(32767 * volume * env * math.sin(phase)))
    return bytes(frames)


def write_wav(path: Path, data: bytes) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data)


def main(root: Path) -> None:
    # Spaceship: rising sweeps, one base pitch per button.
    space = root / "spaceship"
    (space / "theme.json").parent.mkdir(parents=True, exist_ok=True)
    if not (space / "theme.json").exists():
        (space / "theme.json").write_text(json.dumps({"name": "Spaceship", "icon": "🚀"}, ensure_ascii=False), encoding="utf-8")
    for b in range(1, 6):
        base = 300 + b * 120
        write_wav(space / f"button-{b}" / "zap.wav", tone([(base, base * 2, 0.35)]))
        write_wav(space / f"button-{b}" / "beep-beep.wav", tone([(base * 1.5, base * 1.5, 0.12), (0, 0, 0.06), (base * 1.5, base * 1.5, 0.12)]))
    write_wav(space / "select.wav", tone([(400, 1200, 0.5)]))

    # Pirate ship: lower, falling "arr" wobbles.
    pirate = root / "pirate-ship"
    if not (pirate / "theme.json").exists():
        pirate.mkdir(parents=True, exist_ok=True)
        (pirate / "theme.json").write_text(json.dumps({"name": "Pirate ship", "icon": "🏴‍☠️"}, ensure_ascii=False), encoding="utf-8")
    for b in range(1, 6):
        base = 150 + b * 60
        write_wav(pirate / f"button-{b}" / "arr.wav", tone([(base * 1.6, base, 0.45)]))
        write_wav(pirate / f"button-{b}" / "ahoy.wav", tone([(base, base * 1.3, 0.2), (base * 1.3, base, 0.25)]))
    write_wav(pirate / "select.wav", tone([(500, 200, 0.5)]))

    # System sounds.
    write_wav(root / "_system" / "startup.wav", tone([(523, 523, 0.12), (659, 659, 0.12), (784, 784, 0.2)]))
    write_wav(root / "_system" / "select.wav", tone([(660, 880, 0.2)]))
    print(f"placeholder themes ready in {root}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "themes"))
