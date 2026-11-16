# Playset hub

The Raspberry Pi service: reads presses from the USB dongle, plays a clip for the active theme, serves the phone UI. Spec: [`../docs/playset-plan.md`](../docs/playset-plan.md).

## Run it on a laptop (no hardware)

```bash
cd hub
uv run python scripts/make_placeholder_themes.py themes   # beeps for spaceship + pirate-ship
uv run python -m playset_hub --stdin                       # type 1-5 + Enter to "press"
```

Open http://localhost:8080. Needs `mpv` on PATH for sound; add `--no-audio` to log clips instead. Every button in the UI's Buttons tab also has an API press at `POST /api/buttons/{id}/press`.

## Bench prototype (phase 1)

1. **Dongle.** Flash [`../firmware/dongle/dongle.ino`](../firmware/dongle/dongle.ino) to a spare S3 (Arduino IDE, board "ESP32S3 Dev Module", *USB CDC On Boot: Enabled*). Open the serial monitor at 115200 and copy the MAC from the `hello` line.
2. **Fake button.** Paste that MAC into `DONGLE_MAC` in [`../firmware/button/button.ino`](../firmware/button/button.ino), set `BUTTON_ID`, wire a tactile switch from GPIO 4 to GND, and flash a second S3. Its serial monitor prints `press seq=… acked in Nms` on each press.
3. **Hub.** Plug the dongle into the Pi and run:

   ```bash
   uv run python -m playset_hub --serial /dev/ttyACM0
   ```

   On Windows the port looks like `COM5`.

Done when press-to-sound feels instant. Measure it: the button's serial line gives wake-to-ack, the hub log timestamps each `play`.

## Install on the Pi

```bash
sudo apt install mpv
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <this repo> ~/spaceteam_irl && cd ~/spaceteam_irl/hub
cp config.example.json config.json          # set max_volume for the room, button names/colors
uv run python scripts/make_placeholder_themes.py themes
sudo cp systemd/playset-hub.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now playset-hub
```

The unit assumes user `pi` and the repo at `/home/pi/spaceteam_irl`; edit it if not. For a stable serial path, swap `/dev/ttyACM0` for the dongle's `/dev/serial/by-id/...` entry.

## Files

| Path | What |
|---|---|
| `config.json` | Hand-edited, optional. **`max_volume` lives here and only here**; the phone UI cannot raise it. Defaults in `config.example.json`. |
| `data/state.json` | Written by the hub: active theme, volume, interrupt/queue, quiet hours. |
| `data/presses.csv` | One row per accepted press: time, button, seq, battery mV, RSSI. |
| `themes/<id>/button-N/*.{mp3,wav,ogg,…}` | Clips. Several per button = random pick, no immediate repeat. |
| `themes/<id>/theme.json` | Optional `{"name": "...", "icon": "🚀"}`. |
| `themes/<id>/select.*` | Optional sound when the theme is picked. |
| `themes/_system/startup.*`, `select.*` | Startup chime and fallback theme-picked sound. |

After adding files by hand, tap **Settings → Reload themes**.

## Behaviour notes

- **Dedupe:** a `(button, seq)` pair seen in the last 2 s is dropped (radio retries).
- **Interrupt vs queue:** interrupt kills the playing clip. Queue holds up to `queue_limit` clips and drops the rest, so a kid mashing a button doesn't build a minute-long backlog.
- **Quiet hours:** presses are logged but silent. Phone actions (theme pick, tap-to-hear) still play, since a parent is holding the phone.
- **Low battery:** below `low_battery_mv` the Buttons tab shows "charge me". A reading of 0 (bench button) shows as unknown.
- **Games:** presses go through `modes.py`. `FreePlayMode` is the default; a mini game is a new `Mode`.

## Tests

```bash
uv run pytest
```

## Not built yet (phase 3)

Recording in the browser, file upload, Piper TTS lines, silence trim, loudness normalization. Browser mic access needs HTTPS: plan on the homelab reverse proxy or Tailscale certs.
