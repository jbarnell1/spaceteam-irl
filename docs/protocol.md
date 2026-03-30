# ESP-NOW Protocol Specification

> **Version:** 0.2.0 (Draft)
>
> This document is the single source of truth for all communication between the Central Hub and Player Tablets. All firmware implementations must conform to this spec.
>
> **See also:** [game-loop.md](game-loop.md) — walks through the full gameplay lifecycle showing when each message fires and how states transition.

---

## Table of Contents

- [Transport Layer](#transport-layer)
- [Multi-Hub Isolation](#multi-hub-isolation)
- [Message Envelope](#message-envelope)
- [Message Categories](#message-categories)
  - [1. Connection & Pairing](#1-connection--pairing)
  - [2. Lobby & Pre-Game](#2-lobby--pre-game)
  - [3. Gameplay — Hub → Tablet](#3-gameplay--hub--tablet)
  - [4. Gameplay — Tablet → Hub](#4-gameplay--tablet--hub)
  - [5. System & Health](#5-system--health)
  - [6. Game End & Post-Game](#6-game-end--post-game)
  - [7. NFC Card Events (Hub Internal → Broadcast)](#7-nfc-card-events)
- [State Machine](#state-machine)
- [Timing & Reliability](#timing--reliability)
- [Payload Size Budget](#payload-size-budget)
- [Companion App Communication (Non-ESP-NOW)](#companion-app-communication)

---

## Transport Layer

| Property | Value |
|---|---|
| Protocol | ESP-NOW (IEEE 802.11, 2.4GHz) |
| Max payload | **250 bytes** per frame |
| Encoding | JSON (UTF-8) |
| Serialization | ArduinoJson or cJSON |
| Addressing | ESP-NOW peer MAC addresses; Hub maintains a peer table |
| Delivery | Best-effort (no built-in ACK at app layer — see [Timing & Reliability](#timing--reliability)) |
| Encryption | ESP-NOW PMK/LMK encryption enabled (Hub-unique LMK per session) |
| Channel | WiFi channel 1–13; Hub auto-selects at boot, tablets scan to find |

---

## Multi-Hub Isolation

When multiple Hubs operate in the same physical space, three layers prevent cross-talk:

### Layer 1: WiFi Channel Separation (Physical)

Each Hub selects a WiFi channel when entering pairing mode:
1. Hub performs a quick passive scan (~200ms) across channels 1, 6, and 11 (the non-overlapping 2.4GHz channels).
2. Picks the channel with the least ESP-NOW traffic.
3. Falls back to a random choice among {1, 6, 11} if all are quiet.
4. Broadcasts on that channel only.

Tablets in `SEEKING` state **cycle through channels 1, 6, 11** (one per `JOIN_REQ` attempt, rotating every 1s). This means a tablet finds any Hub within 3 seconds regardless of channel.

Once paired via `JOIN_ACK`, the tablet locks to the Hub's channel.

**Effect:** Two Hubs on different channels are completely invisible to each other at the radio layer. This alone solves the problem ~67% of the time (2 of 3 channel choices differ).

### Layer 2: ESP-NOW Encryption (Cryptographic)

Each Hub generates a random **16-byte LMK (Local Master Key)** when entering pairing mode. This key is:
- Sent to the tablet inside the `JOIN_ACK` message (the one unencrypted exchange).
- Used by both Hub and tablet for all subsequent ESP-NOW communication.

After pairing, ESP-NOW encrypts every frame with the session LMK. A tablet paired with Hub A **cannot decrypt** frames from Hub B — they're silently dropped by the ESP-NOW stack before reaching application code.

**Effect:** Even if two Hubs land on the same channel, encrypted traffic from the wrong Hub is gibberish and auto-rejected.

### Layer 3: Session ID Filter (Application)

Each Hub generates a **4-character alphanumeric session ID** (e.g., `"K7X2"`) displayed on the Hub's 7-segment or announced by speaker. This is a human-readable identifier and an application-level safety net.

- The `sid` field is included in `JOIN_REQ` (empty on first attempt, then set after ACK) and `JOIN_ACK`.
- All Hub → Tablet broadcasts include `sid`.
- Tablets drop any message where `sid` doesn't match their paired session.

**Effect:** Even in the unlikely failure of both Layer 1 and Layer 2, application-level filtering catches it. Also gives players a visual way to confirm they're connecting to the right Hub ("connect to Hub K7X2").

### Pairing Flow with Isolation

```
Tablet                           Hub A (ch6, sid:K7X2)        Hub B (ch11, sid:M3P9)
  │                                │                            │
  │── JOIN_REQ (ch1) ────────────►│  (no match, wrong ch)      │
  │── JOIN_REQ (ch6) ────────────►│  ✓ received                │
  │                                │── validates                │
  │◄── JOIN_ACK (sid:K7X2, lmk)──│                            │
  │                                │                            │
  │  [locks to ch6, stores LMK]    │                            │
  │  [all further msgs encrypted]  │                            │
  │                                │                            │
  │── HB (encrypted, sid:K7X2) ──►│  ✓ decrypts               │
  │                                │                            │
  │         (Hub B broadcast)      │                            │
  │◄──────────────────────────────────── LOBBY_STATE (ch11) ───│
  │  [wrong channel — never received]                           │
  │                                │                            │
```

If both Hubs happen to be on the same channel:

```
Tablet (paired to Hub A)         Hub A (ch6, sid:K7X2)        Hub B (ch6, sid:M3P9)
  │                                │                            │
  │◄── encrypted msg (LMK-A) ────│  ✓ decrypts correctly      │
  │◄── encrypted msg (LMK-B) ──────────────────────────────────│
  │  [decryption fails — dropped by ESP-NOW stack]              │
  │                                │                            │
```

---

## Message Envelope

Every message is a JSON object. All messages share a common envelope:

### Tablet → Hub

```json
{
  "type": "<MESSAGE_TYPE>",
  "id": <player_id>,
  "ts": <millis_timestamp>,
  ...payload fields
}
```

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Message type discriminator (see below) |
| `id` | `uint8` | Player ID (0 = unassigned, 1–8 = assigned) |
| `ts` | `uint32` | Sender's `millis()` timestamp |

### Hub → Tablet

```json
{
  "type": "<MESSAGE_TYPE>",
  "target": <player_id_or_"all">,
  ...payload fields
}
```

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Message type discriminator |
| `target` | `uint8` or `"all"` | Recipient player ID, or `"all"` for broadcast |

---

## Message Categories

### 1. Connection & Pairing

These messages handle the initial handshake when a tablet powers on and joins a Hub session.

---

#### `JOIN_REQ` — Tablet → Hub

Tablet broadcasts a join request after boot. Sent repeatedly (every 1s) until acknowledged.

```json
{
  "type": "JOIN_REQ",
  "id": 0,
  "ts": 4521,
  "arch": "NAVIGATOR",
  "fw": "1.2.0",
  "mac": "AA:BB:CC:DD:EE:FF",
  "sid": ""
}
```

| Field | Type | Description |
|---|---|---|
| `arch` | `string` | Archetype ID: `NAVIGATOR`, `ENGINEER`, `OPERATOR`, `SENTINEL`, `MEDIC`, `ANALYST`, `SCOUT`, `COMMANDER` |
| `fw` | `string` | Firmware version (semver) |
| `mac` | `string` | Tablet's MAC address (for Hub peer table) |
| `sid` | `string` | Session ID (empty on first join; set to paired Hub's SID on reconnect attempts) |

---

#### `JOIN_ACK` — Hub → Tablet

Hub accepts the tablet and assigns a player ID.

```json
{
  "type": "JOIN_ACK",
  "target": 1,
  "pid": 1,
  "sid": "K7X2",
  "lmk": "base64-encoded-16-byte-key",
  "ch": 6,
  "color": [0, 255, 128],
  "tone": 3,
  "vibe": 2,
  "name": "Navigator"
}
```

| Field | Type | Description |
|---|---|---|
| `pid` | `uint8` | Assigned player ID (1–8) |
| `sid` | `string` | Hub's session ID (4 alphanumeric chars) |
| `lmk` | `string` | Base64-encoded 16-byte LMK for encrypted communication |
| `ch` | `uint8` | WiFi channel to lock to (1–13) |
| `color` | `[r,g,b]` | RGB values for this tablet's Status LED |
| `tone` | `uint8` | Index into the identification jingle table |
| `vibe` | `uint8` | Index into the vibration pattern table |
| `name` | `string` | Human-readable role name for display |

---

#### `JOIN_DENY` — Hub → Tablet

Hub rejects a join (lobby full, duplicate archetype, game in progress, etc.).

```json
{
  "type": "JOIN_DENY",
  "target": 0,
  "reason": "LOBBY_FULL"
}
```

| `reason` values | Description |
|---|---|
| `LOBBY_FULL` | 8 tablets already connected |
| `GAME_ACTIVE` | A game is in progress; no late joins |
| `ARCH_TAKEN` | Another tablet with this archetype already connected |
| `FW_MISMATCH` | Tablet firmware is incompatible with Hub |

---

#### `LEAVE` — Tablet → Hub

Tablet is intentionally powering down or leaving.

```json
{
  "type": "LEAVE",
  "id": 3,
  "ts": 89210
}
```

---

#### `KICK` — Hub → Tablet

Hub forcibly removes a tablet (admin action via app, or error recovery).

```json
{
  "type": "KICK",
  "target": 3,
  "reason": "ADMIN"
}
```

| `reason` values | Description |
|---|---|
| `ADMIN` | Removed by companion app / host |
| `TIMEOUT` | Missed too many heartbeats |
| `ERROR` | Unrecoverable communication error |

---

### 2. Lobby & Pre-Game

After joining, tablets sit in a lobby waiting for the game to start.

---

#### `LOBBY_STATE` — Hub → All

Broadcast periodically (every 2s) so all tablets know lobby status. Also sent on any change.

```json
{
  "type": "LOBBY_STATE",
  "target": "all",
  "players": [
    {"pid": 1, "arch": "NAVIGATOR", "ready": true},
    {"pid": 2, "arch": "ENGINEER", "ready": false}
  ],
  "scenario": "SPACE_BATTLE_01",
  "nfc": true
}
```

| Field | Type | Description |
|---|---|---|
| `players` | `array` | List of connected players, their archetype, and ready state |
| `scenario` | `string` or `null` | Currently loaded scenario ID (null if no NFC card) |
| `nfc` | `bool` | Whether an NFC card is currently placed on the Hub |

---

#### `READY` — Tablet → Hub

Player presses crisis button to signal ready.

```json
{
  "type": "READY",
  "id": 1,
  "ts": 15230
}
```

---

#### `UNREADY` — Tablet → Hub

Player lifts crisis button cover (cancels ready).

```json
{
  "type": "UNREADY",
  "id": 1,
  "ts": 15890
}
```

---

#### `OLED_LABELS` — Hub → Tablet

Hub pushes narrative labels to a tablet's 9 OLED displays (7 universal + 2 specialty). Sent once when scenario loads, and potentially mid-game if labels change.

```json
{
  "type": "OLED_LABELS",
  "target": 1,
  "labels": [
    "Port Thruster",
    "Stbd Thruster",
    "Drift Brake",
    "Mark Waypoint",
    "Flare Launch",
    "Sensor Ping",
    "Dock Clamp",
    "Helm Control",
    "Thrust Lever"
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `labels` | `string[9]` | Display text for each OLED, ordered: toggle_1, toggle_2, toggle_3, button_1–4, specialty_a, specialty_b |

---

#### `GAME_COUNTDOWN` — Hub → All

Starts a visible countdown before gameplay begins.

```json
{
  "type": "GAME_COUNTDOWN",
  "target": "all",
  "seconds": 5
}
```

---

#### `GAME_START` — Hub → All

Gameplay begins. Sent at countdown=0.

```json
{
  "type": "GAME_START",
  "target": "all",
  "phase": "INTRO",
  "scenario": "SPACE_BATTLE_01",
  "duration": 180
}
```

| Field | Type | Description |
|---|---|---|
| `phase` | `string` | `INTRO`, `FRANTIC`, `WRAPUP` |
| `scenario` | `string` | Active scenario ID |
| `duration` | `uint16` | Total game duration in seconds (for timer display) |

---

### 3. Gameplay — Hub → Tablet

Commands and feedback sent to tablets during active play.

---

#### `COMMAND` — Hub → Tablet

The core gameplay message. Pushes a command to a tablet's command screen.

```json
{
  "type": "COMMAND",
  "target": 2,
  "cmd_id": "cmd_0042",
  "action": "SET_SLIDER",
  "slot": "specialty_a",
  "value": 75,
  "label": "Set thrust to 75%",
  "timeout": 8000,
  "mode": "DIRECT"
}
```

| Field | Type | Description |
|---|---|---|
| `cmd_id` | `string` | Unique command instance ID (for matching responses) |
| `action` | `string` | Control action type (see [Action Types](#action-types) below) |
| `slot` | `string` | Slot name: `toggle_1`–`toggle_3`, `button_1`–`button_4`, `specialty_a`, `specialty_b` |
| `value` | varies | Target value (depends on action type) |
| `label` | `string` | Human-readable text to display on command screen |
| `timeout` | `uint16` | Milliseconds until command expires (0 = no timeout) |
| `mode` | `string` | `DIRECT` (for this player), `COOP` (shout to another player), or `OPEN` (first correct responder wins) |

##### Action Types

| `action` | Expected input | `value` format |
|---|---|---|
| `SET_TOGGLE` | Flip a toggle switch | `bool` (true/false) |
| `PRESS_BUTTON` | Press a specific button | `null` (just press it) |
| `SET_SLIDER` | Move slider to position | `uint8` (0–100 percent) |
| `SET_ENCODER` | Scroll encoder to value | `int16` (target position) |
| `SET_ROTARY_SW` | Turn rotary switch to position | `uint8` (1–6, discrete position) |
| `PLUG_JACK` | Plug barrel jack wires into ports | `{"port": uint8, "wire": string}` |
| `SET_JOYSTICK` | Move joystick to position | `{"x": int8, "y": int8}` (-100 to 100 per axis) |
| `MATCH_COLOR` | Match RGB dial to target | `[r,g,b]` |
| `ENTER_CODE` | Type a code on number pad | `string` (e.g., `"4231"`) |
| `SCAN_NFC` | Scan an NFC card (Sentinel/Commander) | `string` (expected card ID) |
| `CRISIS_BTN` | Press the crisis button | `null` |

---

#### `COOP_COMMAND` — Hub → Tablet

A command that appears on this tablet's screen but is meant for *another* player. The recipient must shout it across the table.

```json
{
  "type": "COOP_COMMAND",
  "target": 1,
  "cmd_id": "cmd_0043",
  "for_player": 3,
  "for_role": "Engineer",
  "label": "Tell the Engineer to close safety valve 2!",
  "timeout": 10000
}
```

| Field | Type | Description |
|---|---|---|
| `for_player` | `uint8` | The player ID who should actually perform the action |
| `for_role` | `string` | Human-readable role name (for the shouted instruction) |
| `label` | `string` | Full text to display on this tablet's command screen |

---

#### `CRISIS` — Hub → All

Triggers a ship-wide crisis event. All players must respond.

```json
{
  "type": "CRISIS",
  "target": "all",
  "cmd_id": "crisis_007",
  "label": "HULL BREACH! ALL HANDS BRACE!",
  "action": "CRISIS_BTN",
  "timeout": 5000,
  "siren": true,
  "vibe": true
}
```

| Field | Type | Description |
|---|---|---|
| `siren` | `bool` | Trigger alarm sound on tablet speaker |
| `vibe` | `bool` | Trigger continuous vibration until resolved |

---

#### `CMD_RESULT` — Hub → Tablet

Feedback after a command is resolved (success, fail, timeout).

```json
{
  "type": "CMD_RESULT",
  "target": 2,
  "cmd_id": "cmd_0042",
  "result": "SUCCESS",
  "points": 10,
  "msg": "Thrust stabilized!"
}
```

| `result` values | Description |
|---|---|
| `SUCCESS` | Player performed the action correctly in time |
| `FAIL` | Player performed the wrong action or wrong value |
| `TIMEOUT` | Command expired before player acted |
| `PARTIAL` | Value was close but not exact (analog controls) |

---

#### `CMD_CANCEL` — Hub → Tablet

Cancels a pending command (e.g., game phase changed, crisis overrides it).

```json
{
  "type": "CMD_CANCEL",
  "target": 2,
  "cmd_id": "cmd_0042"
}
```

---

#### `SCREEN_TEXT` — Hub → Tablet

Generic text push to the tablet's command screen (narration, flavor text, phase transitions).

```json
{
  "type": "SCREEN_TEXT",
  "target": 1,
  "text": "Entering asteroid field...",
  "style": "NARRATION",
  "duration": 4000
}
```

| `style` values | Description |
|---|---|
| `NARRATION` | Story/flavor text (normal font) |
| `ALERT` | Warning text (bold, maybe color) |
| `SUCCESS` | Positive feedback (green tint) |
| `FAIL` | Negative feedback (red tint) |
| `CLEAR` | Clear the screen |

---

#### `PHASE_CHANGE` — Hub → All

Transitions the game to a new phase.

```json
{
  "type": "PHASE_CHANGE",
  "target": "all",
  "phase": "FRANTIC",
  "remaining": 120
}
```

| `phase` values | Description |
|---|---|
| `INTRO` | Narrative introduction, scene-setting |
| `PREFLIGHT` | Pre-flight systems check — crew onboarding |
| `FRANTIC` | Active gameplay — commands firing |
| `WRAPUP` | Debrief, scores, educational content |

---

#### `HAPTIC` — Hub → Tablet

Triggers a specific haptic/audio feedback effect.

```json
{
  "type": "HAPTIC",
  "target": 2,
  "vibe": 5,
  "tone": 0,
  "duration": 300
}
```

| Field | Type | Description |
|---|---|---|
| `vibe` | `uint8` | Vibration pattern index (0 = none) |
| `tone` | `uint8` | Speaker tone index (0 = none) |
| `duration` | `uint16` | Duration in ms (overrides pattern length if set) |

---

#### `SCORE_UPDATE` — Hub → Tablet

Pushes current score/health to a specific tablet or all.

```json
{
  "type": "SCORE_UPDATE",
  "target": "all",
  "health": 72,
  "score": 340,
  "streak": 5
}
```

| Field | Type | Description |
|---|---|---|
| `health` | `uint8` | Ship/team health (0–100) |
| `score` | `uint16` | Current score |
| `streak` | `uint8` | Consecutive successful commands |

---

### 4. Gameplay — Tablet → Hub

State changes and player input reported during active play.

---

#### `STATE` — Tablet → Hub

The primary input message. Sent on any control state change.

```json
{
  "type": "STATE",
  "id": 2,
  "ts": 52340,
  "slot": "specialty_a",
  "ctrl": "SLIDER",
  "val": 75
}
```

| Field | Type | Description |
|---|---|---|
| `slot` | `string` | Which control slot changed (`toggle_1`–`toggle_3`, `button_1`–`button_4`, `specialty_a`, `specialty_b`) |
| `ctrl` | `string` | Control type (see below) |
| `val` | varies | New value |

##### Control Types & Value Formats

| `ctrl` | `val` type | Notes |
|---|---|---|
| `TOGGLE` | `bool` | true = on, false = off |
| `BUTTON` | `bool` | true = pressed, false = released |
| `SLIDER` | `uint8` | 0–100 (percent) |
| `ENCODER` | `int16` | Absolute position or delta (TBD) |
| `ROTARY_SW` | `uint8` | 1–6 (discrete position) |
| `PATCH_BAY` | `[uint8, uint8, uint8]` | Wire ID per port (0 = empty), e.g., `[1, 3, 0]` |
| `JOYSTICK` | `{"x": int8, "y": int8}` | -100 to 100 per axis |
| `COLOR_DIAL` | `[r,g,b]` | Current matched color |
| `KEYPAD` | `string` | Entered sequence (e.g., `"4231"`) |
| `NFC_SCAN` | `string` | Scanned card ID |

---

#### `SUBMIT` — Tablet → Hub

Player presses the Submit button to lock in a value (prevents spam on analog controls).

```json
{
  "type": "SUBMIT",
  "id": 2,
  "ts": 52890,
  "cmd_id": "cmd_0042",
  "slot": "specialty_a",
  "ctrl": "SLIDER",
  "val": 75
}
```

| Field | Type | Description |
|---|---|---|
| `cmd_id` | `string` | The command this submission is responding to (if known) |

---

#### `CRISIS_BTN` — Tablet → Hub

Player presses the crisis button (crisis response or ready toggle).

```json
{
  "type": "CRISIS_BTN",
  "id": 2,
  "ts": 53100,
  "pressed": true
}
```

---

#### `HEARTBEAT` — Tablet → Hub

Sent every 500ms as a keep-alive. Also carries current battery level.

```json
{
  "type": "HB",
  "id": 2,
  "ts": 54000,
  "bat": 78,
  "rssi": -45
}
```

| Field | Type | Description |
|---|---|---|
| `bat` | `uint8` | Battery level (0–100 percent, estimated from voltage) |
| `rssi` | `int8` | Last received signal strength from Hub |

---

### 5. System & Health

Operational messages for monitoring, diagnostics, and error handling.

---

#### `LOW_BATTERY` — Tablet → Hub

Sent when battery drops below warning threshold (~20%). Hub may display warning, announce it, or factor it into game logic.

```json
{
  "type": "LOW_BAT",
  "id": 3,
  "ts": 120000,
  "bat": 15
}
```

---

#### `LOW_BAT_WARN` — Hub → Tablet

Hub instructs a tablet to display a low battery warning (e.g., flash LED, screen icon).

```json
{
  "type": "LOW_BAT_WARN",
  "target": 3,
  "bat": 15
}
```

---

#### `PING` — Hub → Tablet

Hub pings a specific tablet to check responsiveness (on-demand, not periodic).

```json
{
  "type": "PING",
  "target": 2,
  "seq": 42
}
```

---

#### `PONG` — Tablet → Hub

Response to a Hub ping.

```json
{
  "type": "PONG",
  "id": 2,
  "ts": 130500,
  "seq": 42
}
```

---

#### `ERROR` — Either direction

Reports a fault condition.

```json
{
  "type": "ERROR",
  "id": 2,
  "ts": 140000,
  "code": "I2C_FAIL",
  "msg": "OLED slot 3 not responding",
  "slot": 3
}
```

| `code` values | Description |
|---|---|
| `I2C_FAIL` | I2C peripheral not responding |
| `DISPLAY_FAIL` | Screen or OLED render failure |
| `CONTROL_FAIL` | A control input is stuck or disconnected |
| `MEMORY_LOW` | Free heap below safe threshold |
| `NFC_FAIL` | NFC reader error (Hub or Shield Tech tablet) |
| `UNKNOWN` | Catch-all |

---

#### `FW_INFO` — Either direction

Firmware version exchange. Sent during handshake or on request.

```json
{
  "type": "FW_INFO",
  "id": 2,
  "ts": 500,
  "fw": "1.2.0",
  "hw": "TABLET_R2",
  "arch": "NAVIGATOR"
}
```

| Field | Type | Description |
|---|---|---|
| `fw` | `string` | Firmware version (semver) |
| `hw` | `string` | Hardware revision identifier |

---

#### `SYNC_TIME` — Hub → All

Hub broadcasts its own millis value so tablets can calculate clock offset for latency estimation.

```json
{
  "type": "SYNC_TIME",
  "target": "all",
  "hub_ts": 3005000
}
```

---

### 6. Game End & Post-Game

---

#### `GAME_OVER` — Hub → All

Game has ended (win, lose, or NFC card removed).

```json
{
  "type": "GAME_OVER",
  "target": "all",
  "result": "WIN",
  "score": 1250,
  "health": 12,
  "duration": 174,
  "reason": "COMPLETED"
}
```

| `result` values | Description |
|---|---|
| `WIN` | Team survived the scenario |
| `LOSE` | Health reached 0 or critical failure |
| `ABORT` | Game stopped (NFC removed, host action) |

| `reason` values | Description |
|---|---|
| `COMPLETED` | All phases finished naturally |
| `HEALTH_ZERO` | Ship/team health hit 0 |
| `NFC_REMOVED` | NFC card pulled off Hub mid-game |
| `HOST_ABORT` | Host stopped game via button or app |
| `TIMEOUT` | Game timer expired |

---

#### `SCORE_SUMMARY` — Hub → All

Detailed post-game breakdown.

```json
{
  "type": "SCORE_SUMMARY",
  "target": "all",
  "total": 1250,
  "players": [
    {"pid": 1, "correct": 12, "missed": 2, "avg_ms": 2400},
    {"pid": 2, "correct": 10, "missed": 4, "avg_ms": 3100}
  ],
  "crises_survived": 3,
  "streak_best": 8
}
```

| Field | Type | Description |
|---|---|---|
| `players[].correct` | `uint8` | Commands completed successfully |
| `players[].missed` | `uint8` | Commands failed or timed out |
| `players[].avg_ms` | `uint16` | Average response time in milliseconds |
| `crises_survived` | `uint8` | How many shared crises the team survived |
| `streak_best` | `uint8` | Longest consecutive success streak (team-wide) |

---

#### `RETURN_LOBBY` — Hub → All

Transition back to lobby state.

```json
{
  "type": "RETURN_LOBBY",
  "target": "all"
}
```

---

#### `POWER_DOWN` — Hub → All

Hub is shutting down. Tablets should enter low-power or off state.

```json
{
  "type": "POWER_DOWN",
  "target": "all"
}
```

---

### 7. NFC Card Events

These are Hub-internal events that result in broadcasts to tablets.

---

#### `NFC_PLACED` — Hub → All

An NFC game card was placed on the Hub.

```json
{
  "type": "NFC_PLACED",
  "target": "all",
  "card_id": "SPACE_BATTLE_01",
  "title": "Space Battle: Kepler Run",
  "pack": "core_space"
}
```

---

#### `NFC_REMOVED` — Hub → All

The NFC card was removed. If a game is active, this triggers a pause or abort.

```json
{
  "type": "NFC_REMOVED",
  "target": "all",
  "was_active": true
}
```

| Field | Type | Description |
|---|---|---|
| `was_active` | `bool` | Whether a game was in progress when the card was removed |

---

#### `NFC_UNKNOWN` — Hub → All (or internal)

An unrecognized NFC card was placed.

```json
{
  "type": "NFC_UNKNOWN",
  "target": "all",
  "raw_id": "04:A2:C8:1A:5E:00:00"
}
```

---

## State Machine

### Hub States

```
IDLE → PAIRING → LOBBY → COUNTDOWN → GAME_INTRO → GAME_PREFLIGHT → GAME_FRANTIC → GAME_WRAPUP → SCORE → LOBBY
                   ↑                                                                                       │
                   └───────────────────────────────────────────────────────────────────────────────────────────┘
```

| State | Description | Transitions |
|---|---|---|
| `IDLE` | Powered on, no session active | → `PAIRING` (button press) |
| `PAIRING` | Accepting tablet connections | → `LOBBY` (at least 1 tablet joined) |
| `LOBBY` | Players joining, readying, NFC card placed | → `COUNTDOWN` (all ready + NFC present) |
| `COUNTDOWN` | 3-2-1 countdown | → `GAME_INTRO` |
| `GAME_INTRO` | Narration / scene-setting phase | → `GAME_PREFLIGHT` |
| `GAME_PREFLIGHT` | Pre-flight systems check (crew onboarding) | → `GAME_FRANTIC` |
| `GAME_FRANTIC` | Active command phase | → `GAME_WRAPUP` (timer) or `SCORE` (health=0) |
| `GAME_WRAPUP` | Debrief / educational phase | → `SCORE` |
| `SCORE` | Post-game summary | → `LOBBY` |

**NFC removal during `GAME_*`:** Immediately transitions to `SCORE` with `result: ABORT`.

**Tablet disconnect during `GAME_*`:** Game continues with remaining players. Hub stops sending commands to that player. If all tablets disconnect, transition to `IDLE`.

### Tablet States

```
BOOT → SEEKING → JOINED → READY → IN_GAME → POST_GAME → JOINED
                    ↑                                        │
                    └────────────────────────────────────────┘
```

| State | Description | Transitions |
|---|---|---|
| `BOOT` | Power on, hardware init | → `SEEKING` |
| `SEEKING` | Broadcasting `JOIN_REQ` every 1s | → `JOINED` (on `JOIN_ACK`) |
| `JOINED` | In lobby, not ready | → `READY` (crisis button press) |
| `READY` | In lobby, ready | → `JOINED` (unready) or `IN_GAME` (on `GAME_START`) |
| `IN_GAME` | Active gameplay | → `POST_GAME` (on `GAME_OVER`) |
| `POST_GAME` | Viewing score | → `JOINED` (on `RETURN_LOBBY`) |

---

## Timing & Reliability

### Heartbeat

- Tablets send `HB` every **500ms**.
- Hub considers a tablet **disconnected** after **3 missed heartbeats** (1.5s of silence).
- On disconnect, Hub sends `KICK` with `reason: TIMEOUT` and removes from peer table.

### Command Timeout

- Each `COMMAND` includes a `timeout` field (ms).
- If the Hub receives no valid `SUBMIT` or `STATE` matching the `cmd_id` within that window, it auto-resolves as `TIMEOUT` and sends `CMD_RESULT`.

### Delivery & Retries

- ESP-NOW is best-effort. Critical messages use **application-level acknowledgment**:
  - `JOIN_REQ` → expects `JOIN_ACK` / `JOIN_DENY` (tablet retries at 1s intervals)
  - `COMMAND` → expects `STATE` or `SUBMIT` within timeout (no retry; timeout = fail)
  - `LOBBY_STATE` → repeated every 2s (idempotent, self-healing)
  - `HB` → repeated every 500ms (loss of a few is tolerated; 3 missed = disconnect)
- Non-critical messages (haptics, screen text, score updates) are fire-and-forget.

### Clock Synchronization

- Hub periodically sends `SYNC_TIME` (every 30s and once during handshake).
- Tablets compute `offset = hub_ts - local_ts` and include corrected `ts` in reports.
- This allows the Hub to measure true input latency: `latency = hub_receive_ts - tablet_ts - offset`.

---

## Payload Size Budget

ESP-NOW max: **250 bytes**. JSON with short keys keeps us well under budget.

| Message | Typical Size | Notes |
|---|---|---|
| `HB` | ~45 bytes | Sent most frequently |
| `STATE` | ~55 bytes | Per control change |
| `SUBMIT` | ~70 bytes | Includes cmd_id |
| `COMMAND` | ~120 bytes | Largest common gameplay message |
| `OLED_LABELS` | ~210 bytes | 9 short strings; keep labels ≤ 16 chars each |
| `LOBBY_STATE` | ~160 bytes | Grows with player count; 8 players approaches limit |
| `SCORE_SUMMARY` | ~200 bytes | Post-game only; can afford to be larger |
| `COOP_COMMAND` | ~110 bytes | |

**Hard rule:** No single message may exceed 250 bytes. If a message risks exceeding this (e.g., `LOBBY_STATE` with 8 verbose entries), use abbreviated keys or split into multiple frames.

### Key Abbreviation Strategy (if needed)

If payload size becomes tight, switch to abbreviated keys:

| Full key | Short key |
|---|---|
| `type` | `t` |
| `target` | `tg` |
| `id` | `i` |
| `ts` | `s` |
| `slot` | `sl` |
| `value`/`val` | `v` |
| `cmd_id` | `c` |

This is a fallback — start with readable keys while prototyping.

---

## Companion App Communication

The companion app communicates with the Hub via **BLE** or **USB Serial** — NOT via ESP-NOW. This is a separate transport layer used primarily for **initial setup**.

| Function | Direction | Notes |
|---|---|---|
| WiFi setup | App → Hub | Configure home WiFi credentials for Hub direct downloads |
| Game pack upload | App → Hub | Transfer scenario JSON/audio data to Hub flash (fallback if no WiFi) |
| Firmware update | App → Hub | OTA update via BLE or USB |
| Hub configuration | App ↔ Hub | Settings read/write |
| Status query | App ← Hub | Connected tablets, battery levels, active scenario, storage usage |
| Storage management | App ↔ Hub | View cached packs, remove packs to free space |
| Kick player | App → Hub | Admin removal of a tablet |
| Start/stop game | App → Hub | Alternative to physical button |

## Hub Direct Download (WiFi)

After initial WiFi setup via the companion app, the Hub can download content autonomously:

1. **NFC card tapped** → Hub reads scenario ID → checks internal flash for scenario JSON and SPI NAND for audio.
2. **If content missing** → Hub connects to WiFi → authenticates with cloud API → downloads scenario JSON + narrator audio → writes to flash/NAND → loads scenario.
3. **All content permanently cached** — subsequent taps play instantly from local storage.
4. **No phone needed** after WiFi is configured. Hub operates like a Toniebox.
5. **WiFi unavailable at download time** → Hub shows "Connect to WiFi to download this pack" on tablets. Existing cached content still plays fine.

The Hub uses WiFi in STA mode for downloads. During active gameplay, WiFi is repurposed for ESP-NOW. Downloads only happen between games (lobby state).

The companion app protocol and cloud API are **out of scope** for this document and will be specified separately.
