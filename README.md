# Playset Buttons (alpha)

Five big wireless buttons stuck to the kids' indoor playset. Press one and a hub speaker plays a sound that fits the current theme: spaceship, pirate ship, and more. Pick the theme from a phone. Mini games come later on the same hardware.

This repo started as **Spaceteam IRL**, a party game with a hub and up to 8 controller tablets. That design is parked in [`docs/legacy/`](docs/legacy/party-game-README.md). The alpha is deliberately small: one hub, five buttons, sounds on press, themes from a phone.

Full plan: [`docs/playset-plan.md`](docs/playset-plan.md) · Wire format: [`docs/playset-protocol.md`](docs/playset-protocol.md)

## How it fits together

```
5 buttons ──ESP-NOW──► S3 dongle ──USB──► Raspberry Pi hub ──► amp + speaker
(C3, LiPo,             (acks, prints      (themes, clip picker,
 sleep until press)     JSON lines)        phone web UI)
                                               ▲
                                        phone browser on home Wi-Fi
```

## Where things are

| Path | What |
|---|---|
| [`hub/`](hub/README.md) | Pi hub service (Python, `uv`): reads presses, plays clips, serves the phone UI |
| [`firmware/button/`](firmware/button/) | Button firmware (bench: an S3 with a tactile switch; later: the C3 PCB) |
| [`firmware/dongle/`](firmware/dongle/) | Receiver dongle firmware (spare S3 on the Pi's USB) |
| [`docs/playset-plan.md`](docs/playset-plan.md) | Goals, hardware requirements, safety, build phases, open questions |
| [`docs/playset-protocol.md`](docs/playset-protocol.md) | Button → dongle → hub message formats |
| `docs/legacy/`, `missions/`, `firmware/prototype/`, `hardware/` | Parked party-game work, kept for reference |

## Status

| Phase | State |
|---|---|
| 1. Bench prototype (fake button + dongle + Pi) | Firmware written, not yet flashed |
| 2. Hub v1 (themes, random clips, dedupe, interrupt, chime, systemd) | Written, unit tested |
| 3. Phone UI v1 | Themes, button status, settings done; recording/upload/Piper not started |
| 4. Button PCB | Not started |
| 5. Housings | Not started |
| 6. Install and play | — |
| 7. Mini games | Mode layer in place, no games yet |

## Quick start (bench)

```bash
# 1. Make placeholder beep themes so there's something to hear
cd hub
uv run python scripts/make_placeholder_themes.py themes

# 2. Run the hub with keyboard input instead of the dongle (type 1-5 + Enter)
uv run python -m playset_hub --themes themes --stdin

# 3. Open http://<hub-ip>:8080 on your phone
```

With the dongle plugged in, use `--serial /dev/ttyACM0` instead of `--stdin`. See [`hub/README.md`](hub/README.md) for flashing the dongle and button and installing the systemd service.
