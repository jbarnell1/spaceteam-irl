# Project Guidelines: Playset Buttons (alpha)

## Overview

Five wireless arcade buttons on a kids' indoor playset, one Raspberry Pi hub with a speaker, themes picked from a phone. Read [`docs/playset-plan.md`](docs/playset-plan.md) before making design decisions; it is the spec. Wire formats are in [`docs/playset-protocol.md`](docs/playset-protocol.md).

The original Spaceteam IRL party game (8 tablets, OLEDs, NFC cards, Flutter app, mission scenarios) is **parked**. Its docs live in `docs/legacy/`; `missions/`, `firmware/prototype/`, `hardware/` and the other `docs/*.md` files belong to it. Do not extend that work or apply its rules (S3 tablets, JSON-over-ESP-NOW, OLED labels, archetypes, COGS targets) to the alpha unless asked.

## Architecture

```
Buttons (5) ──ESP-NOW──► Dongle (ESP32-S3) ──USB CDC──► Hub (Raspberry Pi) ──► amp + speaker
                                                             ▲
                                                     phone browser (LAN)
```

- **Buttons are dumb.** Wake on press, send one frame, wait for the ack, sleep. No game logic, no listening (in the alpha).
- **The dongle is a pipe.** It turns ESP-NOW frames into JSON lines. No dedupe, no state.
- **The hub owns everything else:** dedupe, theme, clip choice, playback, settings, logging, UI, and (later) games.

### Key directories

| Path | Contents |
|---|---|
| `hub/` | Hub service: Python package `playset_hub`, tests, systemd unit, placeholder theme generator |
| `firmware/button/` | Button firmware |
| `firmware/dongle/` | Dongle firmware |
| `docs/playset-*.md` | Alpha plan and protocol |

## Code style

### Firmware (ESP32)
- Bench firmware is Arduino-ESP32 (`.ino`), matching the parked prototype. Production button firmware may move to ESP-IDF in phase 4 for sleep-current control.
- `snake_case` functions/variables, `PascalCase` types, `ALL_CAPS` constants and macros. Fixed-size integer types.
- Button → dongle payload is the packed 10-byte struct in `docs/playset-protocol.md`. Change the doc, the button, the dongle, and the hub parser together, and bump `version`.
- No `delay()` in the dongle's receive path. On the button, short waits during the wake cycle are fine; it does nothing else.

### Hub (Python)
- Run everything through **uv** (`uv run ...`), from `hub/`. No venvs or `pip install`.
- Keep game logic behind `modes.py`: the default mode plays the button's clip; games are new modes.
- The audio player and event source are injectable so tests run without hardware or audio. Keep it that way.
- Tests: `cd hub && uv run pytest`.

## Constraints

- **Press-to-sound under ~500 ms.** Don't add work between the serial read and starting playback.
- **Battery life is weeks to months.** Buttons spend almost all their time in deep sleep (target < 20 µA board-wide). Anything that makes a button wake or listen more needs a measured reason.
- **Local only.** No cloud services. The web UI binds to the LAN and has no login in the alpha.
- **Safety is not optional.** Volume has a hard ceiling (`max_volume`, config file only, not settable from the UI). Quiet hours silence the hub. Lithium cells are protected and enclosed; firmware sleeps hard on low battery.
- **Leave room for mini games** (mode layer, button names/colors in config, unpopulated LED MOSFET footprint), but don't build them in the alpha.
