> **Parked.** This is the original Spaceteam IRL party-game design, set aside on 2026-11-16 in favor of the Playset Buttons alpha. See [the current README](../../README.md). Kept for reference; nothing here is in scope for the alpha.

# Project Guidelines — Spaceteam IRL

## Overview

This is a cooperative hardware game project. The system consists of a **Central Hub** (game master) and up to **8 Player Tablets** (fixed-loadout input devices), communicating over **ESP-NOW** (2.4GHz, router-free).

Read [README.md](party-game-README.md) for the full project specification before making design decisions.

## Code Style

### Firmware (C++ / ESP-IDF)
- Target: **ESP32-S3-WROOM-1-N16R8** (16MB flash, 8MB PSRAM) via PlatformIO (ESP-IDF framework)
- Use `snake_case` for functions and variables, `PascalCase` for types/structs, `ALL_CAPS` for constants and macros
- Prefer fixed-size types (`uint8_t`, `int32_t`) over `int`/`long` — this is embedded code
- Keep ISRs minimal — defer work to FreeRTOS tasks via queues
- All ESP-NOW payloads are JSON; use ArduinoJson or cJSON for serialization
- Pin assignments live in a single `pin_config.h` per target (hub or tablet)
- Never use `delay()` in production code; use `vTaskDelay()` or timer-based patterns

### Flutter (Companion App)
- Follow standard Flutter/Dart conventions and `flutter_lints`
- State management approach TBD — keep UI code decoupled from BLE/serial transport
- App handles: WiFi setup (one-time), account login, game pack management (purchase/browse), hub configuration, firmware updates, storage management
- Business model is **buy-once-and-own** — no subscriptions

## Architecture

```
Hub (1)  <──ESP-NOW──>  Tablets (up to 8)
  │                         │
  ├─ Game state machine     ├─ Fixed control loadout per archetype
  ├─ Mission audio (V1)     ├─ OLED label rendering (Hub-pushed)
  ├─ HDMI video out (V2)    ├─ Tablet screen (commands / cross-tablet)
  ├─ NFC game card reader   ├─ State-change event push
  ├─ WiFi (content download)└─ Heartbeat (500ms)
  ├─ 128MB SPI NAND (audio)
  └─ Command dispatch
```

- **Hub** owns all game state. Tablets are stateless input/output nodes.
- Tablets report state changes only (not continuous streams) plus a 500ms heartbeat.
- Each tablet has a **fixed archetype** (e.g., Navigator, Engineer) with a hardcoded control loadout. On connection, the tablet reports its archetype to the Hub.
- The Hub maps archetype + slot to narrative labels and pushes display text to the tablet's per-slot OLEDs.
- Each tablet has a **command screen** that displays directives for the player or cross-tablet commands in chaotic modes.
- Tablets identify themselves to players via **Status RGB LED color**, **speaker tone**, and **vibration pattern** assigned by the Hub.
- Game content loaded via **NFC cards** (tapped on Hub reader) or via the **companion app**.
- Hub connects to home WiFi to auto-download content for new NFC cards (Toniebox-style). No phone needed after initial WiFi setup.
- Narrator audio stored on external **W25N01GV 128MB SPI NAND flash** (permanent cache, not evicted).

### Key Directories

| Path | Contents |
|---|---|
| `firmware/hub/` | Central Hub firmware |
| `firmware/tablet/` | Player Tablet firmware |
| `firmware/shared/` | Shared ESP-NOW protocol, tablet identity, NFC, message types |
| `hardware/pcb/` | EasyEDA / Gerber PCB files |
| `hardware/3d/` | 3D-printable enclosure STL/STEP files |
| `hardware/bom/` | Bills of Materials |
| `app/` | Flutter companion app |
| `missions/` | Mission Architect LLM templates, generated scenarios, and validation pipeline |
| `missions/author_pipeline/` | Author pipeline: compile source format → materialized JSON ([docs](../author-pipeline.md)) |
| `missions/scenarios-src/` | Source-format scenarios (`.src.json`) — what authors edit |
| `missions/scenarios/` | Materialized runtime JSON — compiled output, Hub firmware input |
| `docs/` | Protocol spec, tablet archetypes, manufacturing notes |

## Build and Test

### Firmware
```bash
# Build Hub firmware
cd firmware/hub && pio run

# Build Tablet firmware
cd firmware/tablet && pio run

# Flash to connected device
pio run --target upload

# Run unit tests (native platform)
pio test -e native
```

### Flutter App
```bash
cd app
flutter pub get
flutter run
flutter test
```

### Python Tooling (uv)
All Python scripts use **[uv](https://docs.astral.sh/uv/)** as the runtime — no venvs, no `pip install`, no `requirements.txt`. `uv run` resolves dependencies automatically.

```bash
# Validate a scenario JSON (run from repo root)
uv run python -m missions.validate missions/scenarios/station_omega.json

# Validate + full difficulty & content analysis
uv run python -m missions.validate missions/scenarios/station_omega.json --analyze

# Override difficulty level for analysis
uv run python -m missions.validate missions/scenarios/station_omega.json --analyze -d hard

# Emit resolved JSON with preset difficulty parameters filled in
uv run python -m missions.validate missions/scenarios/station_omega.json --resolve
```

The **author pipeline** lives in `missions/author_pipeline/` and decouples scenario creative content from hardware specifics. Full docs: [`docs/author-pipeline.md`](../author-pipeline.md).

```bash
# Compile source format → materialized runtime JSON
uv run python -m missions.author_pipeline compile missions/scenarios-src/station_omega.src.json -o missions/scenarios/station_omega.json

# Decompile materialized → source format
uv run python -m missions.author_pipeline decompile missions/scenarios/station_omega.json -o missions/scenarios-src/station_omega.src.json

# Round-trip integrity check on all scenarios
uv run python -m missions.author_pipeline roundtrip missions/scenarios/*.json
```

The validation pipeline lives in `missions/validate/` and enforces every rule from `docs/scenario-schema.md`:
- **`capability_matrix.py`** — Hardware truth tables: which archetype+slot supports which action
- **`difficulty_presets.py`** — Four difficulty levels (easy/medium/hard/extreme) with per-phase parameters. Scenarios only declare `meta.difficulty`; all phase tuning resolves from presets.
- **`validator.py`** — Full schema validation (capability compliance, pool coverage, tier balance, timeouts, crises, outcome coverage, label lengths, unique IDs)
- **`analyzer.py`** — Difficulty curves, command distribution, coop network, path timing estimates, and side-by-side difficulty preset comparison

## Conventions

### ESP-NOW Messages
- All payloads are JSON objects with a `"type"` field discriminator
- Max ESP-NOW payload: **250 bytes** — keep messages compact
- Tablet → Hub messages include `"id"` (player ID) and `"ts"` (millis timestamp)
- Hub → Tablet messages include `"cmd"` (command type) and `"target"` (player ID or `"all"`)

### Tablet Archetype Registry
- Every tablet archetype and its control loadout must be documented in `docs/tablet-archetypes.md`
- Each tablet stores its archetype ID in firmware (e.g., `NAVIGATOR`, `ENGINEER`)
- On boot, the tablet reports its archetype to the Hub; the Hub maps controls to narrative labels

### Content Delivery
- Game packs are loaded via NFC cards (physical) or the companion app (digital purchase)
- All game content is buy-once-and-own — no subscription model
- Each game pack contains command maps; the Hub randomly draws from these pools each run for fresh gameplay
- Scenario JSON stored on ESP32-S3 internal flash (16MB). Narrator audio stored on external W25N01GV 128MB SPI NAND flash.
- Hub connects to WiFi to auto-download content when a new/unrecognized NFC card is tapped (Toniebox model)
- All downloaded content is permanently cached — plays fully offline after first download
- Companion app handles initial WiFi setup; Hub operates independently afterwards

### Hardware Design
- PCBs designed in EasyEDA, optimized for JLCPCB SMT assembly
- Prototype enclosures: PLA 3D prints, 8-inch chassis
- Controls are fixed per archetype — soldered/wired to the main PCB (not modular)

### Pin Budget Awareness
- The ESP32-S3 has limited GPIO. Always check `pin_config.h` before claiming pins.
- I2C bus is shared across all 5 OLED displays, the tablet screen (if I2C), and the 7-segment display. Use unique addresses or a TCA9548A mux if conflicts arise.

### Safety and Power
- 2× AA battery sled (~3V nominal) with boost converter to 3.3V (~85% efficiency)
- Estimated ~210–280 mA average draw → ~5–6 hours runtime per set of batteries
- Vibration motor driven via MOSFET, never directly from GPIO

## Important Constraints

- **Latency is king.** ESP-NOW was chosen over WiFi/BLE specifically for sub-10ms delivery. Don't introduce abstractions that add latency to the input→hub path.
- **250-byte payload limit.** ESP-NOW frames max at 250 bytes. Never exceed this; design messages to fit.
- **No continuous streaming.** Tablets push on state-change + 500ms heartbeat only.
- **Hub is authoritative.** Tablets never make game-logic decisions. They report inputs; the Hub decides outcomes.
- **Fixed archetype loadouts.** Each tablet has a hardcoded control set. No runtime peripheral detection or EEPROM scanning.
- **Command randomization.** Each run randomly pulls commands from allowed maps so gameplay stays fresh. Never hardcode a fixed command sequence.
- **Target COGS ~$20/tablet at scale.** Every component choice should consider cost at 1,000+ unit volumes.
