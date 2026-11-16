# Playset Buttons: Project Plan

Source: `Playset Buttons Project Plan.pdf` (Nov 16, 2026). This file is the in-repo copy of that plan and the spec for the alpha. Decisions made while building are recorded under [Decisions](#decisions-made-so-far).

## Overview and goals

Five wireless buttons stick onto the kids' indoor playset. When one is pressed, a hub plays a recording on its speaker that matches the current theme (spaceship, pirate ship, and others). The theme is picked from a phone. Mini games come later, built on the same pieces.

This is a deliberate restart. The earlier version (a family party game with a hub and up to 8 controller tablets, now in [`docs/legacy/`](legacy/party-game-README.md)) got too complicated. The alpha is: one hub, five buttons, sounds on press, themes from a phone.

### Alpha goals

- A press plays its sound in under about 500 ms, so it feels instant to a small child.
- Each button runs on a small rechargeable LiPo, charged over USB-C, and lasts weeks to months between charges.
- Buttons stick to the playset (indoors) with no wires.
- Swapping the theme from a phone changes what every button says.
- Everything runs locally on the home network. No cloud.

### Not in the alpha

- Mini games (the alpha leaves room for them).
- Hub-controlled lights on the buttons.
- Outdoor or weatherproof use.
- Multiple hubs, tablets/controllers, NFC cards, the companion app, or anything else from the party-game design.

## System architecture

```
 5 buttons            receiver dongle         Raspberry Pi hub            amp + speaker
 ESP32-C3, LiPo  ──►  spare ESP32-S3    ──►   theme + clip picker   ──►   spare driver
 wake on press  ESP-NOW  acks each press  USB  serves phone UI             printed housing
                                                   ▲
                                                   │ home Wi-Fi, web page
                                              phone browser
                                     (pick theme, record clips, see battery)
```

- **Button (x5):** custom PCB, ESP32-C series module, big arcade button, LiPo, USB-C charging. Sleeps until pressed, sends one message, sleeps again.
- **Receiver dongle:** a spare ESP32-S3 plugged into the Pi over USB. Receives ESP-NOW, the radio acks each frame, and the dongle prints one JSON line per press over USB CDC.
- **Hub:** Raspberry Pi + I2S/class-D amp + spare speaker driver in a printed enclosure. One Python service: reads button events, picks the clip for the active theme, plays it, serves the phone UI.
- **Phone:** any browser on the home Wi-Fi. No app to install.

### Why this shape

- **ESP-NOW, not Wi-Fi, on the buttons.** Joining Wi-Fi after wake takes 1–3 s. ESP-NOW is connectionless, so a sleeping button can wake, send, and get an ack well under a second, at far less energy per press.
- **A Pi hub, not an all-ESP32 hub.** Mini games, theme management, audio, and a web UI are much easier in Linux. An all-S3 hub (I2S amp, SD card, on-chip web server) is the fallback if no Pi is on hand, but game logic would then live in firmware.
- **The S3 as a dongle.** Native USB means it enumerates as a serial device on the Pi with no USB-UART chip, and it uses up the spare S3 boards.

## Button hardware

Custom PCB from JLCPCB (5-board minimum matches the alpha), assembled at home with stencil + hot plate.

**Chip**
- Default: ESP32-C3 module (e.g. ESP32-C3-MINI-1): cheap, well stocked at LCSC, low deep-sleep current, GPIO wake from deep sleep, built-in USB Serial/JTAG so the USB-C port both charges and flashes.
- Alternative: ESP32-C6 if it shows a clear battery or radio win. Confirm ESP-NOW interop with the S3 dongle before committing.
- Module with antenna, not a bare chip.

**Power**
- 1S LiPo pouch, ~300–500 mAh, sized to the housing, with protection (in-cell or on-board).
- Single-cell charger IC from USB-C, with CC resistors. Charge LED visible through the housing.
- Low-Iq 3.3 V regulator. Whole-board sleep target: **< 20 µA**.
- Battery voltage on an ADC pin through a high-value or switched divider.

**Button and connections**
- Large arcade button (60 mm or 100 mm dome, after a fit check) on a header so it can be swapped.
- Button on a deep-sleep wake-capable GPIO with pull-up, debounced in firmware.
- Unpopulated footprint for driving the arcade button's LED through a MOSFET (unused in the alpha, keeps mini games open without a respin).
- Boot/reset pad or button for flashing recovery.

**Battery life math (verify on the bench).** A press costs a short radio burst for a fraction of a second. At ~200 presses/day plus sleep current, a 400 mAh cell should last many weeks to a few months. Measure real sleep and per-press current on the first board and update this.

**Housing (3D printed)**
- Parametric source (OpenSCAD or CadQuery) plus exported STLs.
- Holds PCB, cell, arcade button. USB-C reachable, charge LED visible.
- Flat back for removable mounting tape or Dual Lock, so a button comes off for charging.
- Screw-closed, not snap-fit. Rounded edges. One print color per button.

## Button firmware

1. Deep sleep with the button GPIO armed as the wake source.
2. On wake, start ESP-NOW on a fixed channel. No Wi-Fi association.
3. Send one message to the dongle's MAC.
4. Wait briefly for the ESP-NOW MAC-layer ack; if none, retry a few times with short backoff.
5. Wait for release (one long press = one event), then deep sleep.

Message fields: protocol version, button ID, sequence number (kept in RTC memory across deep sleep), battery millivolts, event type. Wire format: [`docs/playset-protocol.md`](playset-protocol.md).

Other requirements: measure wake-to-send and keep press-to-sound under ~500 ms; firmware updates over USB-C (no OTA in the alpha); ESP-IDF or Arduino.

## Hub hardware and software

**Hardware:** any Pi with Wi-Fi (Zero 2 W, 3, 4, 5). I2S amp (MAX98357A class) or small class-D amp matched to the spare driver's impedance and power. Hard software volume ceiling. USB power, always plugged in.

**Hub/speaker housing:** parametric source + STL; holds Pi, dongle, amp, driver with sealed or ported back; grille, Pi vents, power cable exit; screw-closed.

**Software** (implemented in [`hub/`](../hub/README.md)):
- One service reading button events from the dongle, playing audio, serving the phone UI.
- Drops duplicate events by button ID + sequence number.
- New press interrupts the playing clip (setting: interrupt or queue).
- Logs each press with time and battery level; flags low batteries.
- Startup chime when ready.

**Themes and sounds.** A theme is a folder; each button has a subfolder with one or more clips. The hub picks at random, avoiding an immediate repeat.

```
themes/
  spaceship/
    theme.json      (display name, icon, optional ambient loop)
    button-1/  launch.mp3, countdown.mp3
    button-2/  shields.mp3
    ...
  pirate-ship/
    ...
```

Clips can be home recordings, sound effects, or Piper TTS.

## Phone UI

Mobile-first page served by the hub, saved to the home screen. Big tap targets, one-handed.

- **Themes:** grid of theme cards; tap to activate; hub plays a confirmation sound.
- **Buttons:** the five buttons with color, battery, last press. Tap to hear its clips for the current theme.
- **Recordings:** pick theme + button, record in browser, upload a file, or type a line for Piper. Preview, trim silence, save, delete.
- **Settings:** volume, interrupt vs queue, quiet hours.

Notes: mic recording needs HTTPS (homelab reverse proxy, Tailscale, or a local cert); voice-memo upload is the fallback. No login on the LAN, but LAN only. Loudness-normalize every saved clip.

## Mini games (later)

The hub runs games; buttons stay simple. Ideas that work with alpha hardware: Captain's orders ("Press the red button!"), Sequence (repeat a growing pattern), Mission story (each button is a choice), Race the clock (press all five).

What the alpha must leave room for:
- Event handling goes through a mode layer; "play the button's clip" is the default mode. (Done: `hub/playset_hub/modes.py`.)
- Each button has a name and color in config. (Done: `buttons` in hub config.)
- The LED footprint on the button PCB. Lighting a button on command needs the button to listen, which costs battery (light sleep during a game, or a short listen window after each press). Not an alpha decision.
- Games started and stopped from the phone UI.

## Safety

Small kids and lithium cells: these are requirements, not suggestions.
- Cell fully enclosed, screw-closed. No access to cell, wires, or PCB without a screwdriver.
- Over-discharge, overcharge, and short-circuit protection.
- Firmware sleeps hard on low battery instead of draining to zero.
- Charge off the playset, on a hard surface, supervised. Never while kids are playing.
- No small parts that can come loose; arcade button captured by the housing; firm mounting.
- PETG or similar (doesn't crack into sharp pieces), rounded edges.
- Software volume cap on the hub, plus quiet hours.

## Build phases

Prove the loop on the bench with parts on hand before ordering boards.

1. **Bench prototype.** Two spare S3 boards: one fake button (tactile switch, USB powered), one dongle. Pi plays a sound on press. Done when press-to-sound feels instant. *Firmware: [`firmware/button/`](../firmware/button/), [`firmware/dongle/`](../firmware/dongle/).*
2. **Hub v1.** Themes folder, random clip selection, dedupe, interrupt setting, startup chime, systemd service. Done when two themes work end to end. *Code: [`hub/`](../hub/).*
3. **Phone UI v1.** Theme picker, button status, recording and upload, Piper lines, volume. Done when a new theme can be built from the phone alone. *Theme picker, button status, and settings exist; recording/upload/Piper do not yet.*
4. **Button PCB.** Schematic, layout, BOM, Gerbers, stencil for 5 boards. Hand-build one first; measure sleep current, per-press current, wake-to-ack.
5. **Housings.** Button and hub/speaker housings, parametric + STL. Test-fit one button before printing five.
6. **Install and play.** Mount, record the first themes with the kids, watch how they use it.
7. **Mini games.** Pick one game, build it, then decide whether button LEDs are worth the battery cost.

## Open questions

For Jonathan:
- [ ] Spare Raspberry Pi on hand, and which model? If not, is the all-S3 hub fallback OK?
- [ ] Spare speaker driver specs (size, impedance, watts); is the "speaker" powered or passive?
- [ ] Arcade button size: 60 mm or 100 mm dome?
- [ ] First themes besides spaceship and pirate ship?
- [ ] Hub reachable from outside the house (via homelab), or LAN only?
- [ ] Link to the old hub-and-controllers chat, if found.

For the coding agent:
- [ ] C3 vs C6 (sleep current, ESP-NOW interop with S3, LCSC stock).
- [ ] JLC assembly of module + fine-pitch parts vs full hand assembly with stencil.
- [x] Pairing approach: see Decisions.
- [ ] Exact cell size once the housing is drafted.

## Decisions made so far

| Decision | Choice | Why |
|---|---|---|
| Button → dongle wire format | 10-byte packed binary struct, not JSON | Smallest airtime and fastest encode on a just-woken chip; the dongle converts to JSON lines for the Pi, which is where readability matters. |
| Pairing (alpha) | Dongle MAC hard-coded at build time (`DONGLE_MAC` in the button sketch) | Simplest thing that works for 5 buttons. Pairing mode can come later without changing the message format. |
| ESP-NOW channel | Fixed channel 1 on both sides | Buttons skip scanning. The dongle never joins Wi-Fi, so the Pi's Wi-Fi channel doesn't matter. |
| Duplicate handling | Hub drops a (button, seq) pair seen in the last 2 s | Catches radio retries, and still accepts presses after a button cold-boots and its sequence counter restarts. |
| Bench firmware | Arduino-ESP32 sketches, matching `firmware/prototype/` | Fastest path to "press-to-sound feels instant". The production C3 firmware can move to ESP-IDF in phase 4 for sleep-current control. |
| Hub audio playback | One `mpv` subprocess per clip (command configurable) | Plays mp3/wav/ogg, has a volume flag, and killing the process is a clean interrupt. |
| Hub web stack | `aiohttp` + one static HTML page, run with `uv` | One async process handles serial, audio, and HTTP; no build step for the UI. |
