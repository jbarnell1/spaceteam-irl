# Gameplay Loop & State Transitions

> Companion document to [protocol.md](protocol.md). This describes *when* and *why* each message fires, walking through the full lifecycle from power-on to power-down.

---

## Table of Contents

- [Overview: The Full Loop](#overview-the-full-loop)
- [Phase 0 — Power On & Discovery](#phase-0--power-on--discovery)
- [Phase 1 — Lobby](#phase-1--lobby)
- [Phase 2 — NFC Card & Scenario Load](#phase-2--nfc-card--scenario-load)
- [Phase 3 — Ready Up & Countdown](#phase-3--ready-up--countdown)
- [Phase 4 — Game: Intro](#phase-4--game-intro)
- [Phase 5 — Game: Frantic](#phase-5--game-frantic)
- [Phase 6 — Game: Wrap-Up](#phase-6--game-wrap-up)
- [Phase 7 — Score & Post-Game](#phase-7--score--post-game)
- [Phase 8 — Return to Lobby / Power Down](#phase-8--return-to-lobby--power-down)
- [Edge Cases & Interrupts](#edge-cases--interrupts)
  - [Tablet Disconnects Mid-Game](#tablet-disconnects-mid-game)
  - [NFC Card Removed Mid-Game](#nfc-card-removed-mid-game)
  - [Low Battery During Play](#low-battery-during-play)
  - [Late Join Attempt](#late-join-attempt)
  - [Duplicate Archetype Conflict](#duplicate-archetype-conflict)
  - [Hub Power Down / Abort](#hub-power-down--abort)
  - [Hardware Fault on Tablet](#hardware-fault-on-tablet)
  - [Multiple Hubs in Same Area](#multiple-hubs-in-same-area)

---

## Overview: The Full Loop

```
┌─────────────────────────────────────────────────────────┐
│                        HUB                              │
│                                                         │
│  IDLE ──► PAIRING ──► LOBBY ──► COUNTDOWN ──► GAME     │
│                         ▲        │             │        │
│                         │        │      ┌──────┘        │
│                         │        │      ▼               │
│                         │        │    INTRO ──► FRANTIC │
│                         │        │                │     │
│                         │        │                ▼     │
│                         │        │             WRAPUP   │
│                         │        │                │     │
│                         │        │                ▼     │
│                         │        │             SCORE    │
│                         │        │                │     │
│                         └────────┴────────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                       TABLET                            │
│                                                         │
│  BOOT ──► SEEKING ──► JOINED ──► READY ──► IN_GAME     │
│                         ▲                     │         │
│                         │                     ▼         │
│                         │                  POST_GAME    │
│                         │                     │         │
│                         └─────────────────────┘         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

The system loops through **Lobby → Game → Score → Lobby** indefinitely. A new game starts whenever all players ready up with an NFC card on the Hub. The Hub can also be powered down from any state.

---

## Phase 0 — Power On & Discovery

**Duration:** Until first tablet joins (~2–10 seconds per tablet)

### What happens

1. **Hub powers on → state `IDLE`.**
   - Runs hardware self-test (speaker, NFC reader, LED).
   - Illuminated button glows steady (indicating "press to pair").
   - No ESP-NOW peers registered.

2. **Host presses the Hub button → state `PAIRING`.**
   - Hub scans WiFi channels 1, 6, 11 and picks the least congested.
   - Hub generates a random **session ID** (4 alphanumeric chars, e.g., `K7X2`) and a **16-byte LMK** encryption key.
   - Hub displays session ID on its 7-segment / announces via speaker: "Hub K-7-X-2 ready."
   - Hub begins listening for `JOIN_REQ` messages on its chosen channel.
   - Hub button pulses (indicating "accepting connections").

3. **Tablet powers on → state `BOOT`.**
   - Hardware init: display test, OLED clear, speaker chirp, LED white pulse.
   - 7-segment shows `--` (no connection).
   - Reads archetype ID from firmware config.

4. **Tablet → state `SEEKING`.**
   - Broadcasts `JOIN_REQ` every 1 second, **rotating through channels 1, 6, 11** (one channel per attempt).
   - This ensures the tablet finds a Hub on any channel within 3 seconds.
   - Status LED pulses white.

5. **Hub receives `JOIN_REQ`.**
   - Validates: archetype not already taken, lobby not full, firmware compatible.
   - If accepted → sends `JOIN_ACK` with player ID, **session ID, LMK, channel number**, LED color, tone, vibe pattern.
   - If rejected → sends `JOIN_DENY` with reason.

6. **Tablet receives `JOIN_ACK` → state `JOINED`.**
   - **Stores the LMK and locks to the Hub's WiFi channel.** All further communication is encrypted.
   - Stores the session ID; drops any future messages with a different `sid`.
   - 7-segment shows assigned player ID (e.g., `1`).
   - Status LED changes to assigned archetype color.
   - Speaker plays identification jingle.
   - Vibration motor plays identification pattern.
   - Stops broadcasting `JOIN_REQ`.
   - Begins sending `HB` (heartbeat) every 500ms (encrypted).

### Message sequence

```
Tablet              Hub
  │                  │
  │── JOIN_REQ (ch1)─►│  (miss — wrong channel)
  │── JOIN_REQ (ch6)─►│  ✓ received
  │                  │── validates
  │◄── JOIN_ACK ─────│  (includes sid, LMK, channel)
  │                  │
  │  [locks to ch6, enables encryption]
  │                  │
  │── HB (encrypted)─►│  (every 500ms from now on)
  │── HB (encrypted)─►│
  │  ...             │
```

---

## Phase 1 — Lobby

**Duration:** Until all players are ready and an NFC card is present

### Hub state: `LOBBY`

Once at least one tablet is in `JOINED`, the Hub transitions from `PAIRING` to `LOBBY`. (The Hub continues accepting new tablets in `LOBBY` — pairing doesn't close until the game starts.)

### What happens

1. **Hub broadcasts `LOBBY_STATE` every 2 seconds.**
   - Contains the list of all connected players, their archetypes, and ready states.
   - Contains whether an NFC card is present and which scenario is loaded.
   - This is idempotent — tablets can reconstruct lobby state from any single message (self-healing after packet loss).

2. **More tablets join** (same Phase 0 handshake, concurrently).
   - Each new `JOIN_ACK` triggers an immediate `LOBBY_STATE` broadcast so all tablets see the update.

3. **Hub sends `SYNC_TIME`** once during this phase (and every 30s thereafter).
   - Tablets compute their clock offset for latency measurement later.

### What tablets display

- 7-segment: Player ID (steady).
- Status LED: Archetype color (steady).
- Command screen: "Waiting for players..." or lobby list.
- OLEDs: Blank or showing generic slot names (no scenario loaded yet).

### Message sequence

```
Hub                       Tablet 1         Tablet 2
 │                          │                │
 │── LOBBY_STATE ─────────►│               │  (every 2s, broadcast)
 │── LOBBY_STATE ──────────────────────────►│
 │                          │                │
 │── SYNC_TIME ───────────►│               │
 │── SYNC_TIME ─────────────────────────────►│
 │                          │                │
```

---

## Phase 2 — NFC Card & Scenario Load

**Duration:** Instant (happens while in Lobby)

### What happens

1. **Player places an NFC card on the Hub.**
   - Hub NFC reader detects the card and reads its scenario ID.
   - If recognized → Hub loads scenario data from internal flash and audio from SPI NAND cache.
   - If unrecognized but Hub has WiFi → Hub auto-downloads the scenario JSON + narrator audio from the cloud, caches permanently to flash, then loads. (Toniebox-style first-tap download.)
   - Hub broadcasts `NFC_PLACED` with card ID, title, and pack name.

2. **Hub pushes `OLED_LABELS` to each connected tablet.**
   - Each tablet gets 5 narrative-appropriate labels for its control OLEDs, based on the scenario theme + the tablet's archetype.
   - E.g., Navigator in "Pirate Hunt" gets: `"Helm"`, `"Spyglass"`, `"Port Sail"`, `"Starboard Sail"`, `"Anchor"`.

3. **Tablets render OLED labels** on their 5 per-slot displays.

4. **Lobby state refreshes** — `LOBBY_STATE` now includes `scenario: "PIRATE_HUNT_01"`, `nfc: true`.

5. **If NFC card is unrecognized and Hub has no WiFi** → Hub broadcasts `NFC_UNKNOWN`. Tablets/command screens show "Unknown card — connect to WiFi to download". No scenario loads.

### What tablets display

- OLEDs: Scenario-specific labels (pushed by Hub).
- Command screen: Scenario title and "Ready up to begin!"
- 7-segment: Player ID (unchanged).

### Message sequence

```
Hub                         Tablet 1              Tablet 2
 │                            │                     │
 │  [NFC card placed]         │                     │
 │── NFC_PLACED ────────────►│                    │
 │── NFC_PLACED ──────────────────────────────────►│
 │                            │                     │
 │── OLED_LABELS ───────────►│  (5 labels for Navigator)
 │── OLED_LABELS ──────────────────────────────────►│  (5 labels for Engineer)
 │                            │                     │
 │── LOBBY_STATE ───────────►│                    │  (now includes scenario)
 │── LOBBY_STATE ──────────────────────────────────►│
```

---

## Phase 3 — Ready Up & Countdown

**Duration:** Player-dependent + 5-second countdown

### What happens

1. **Players flip their crisis button covers and press.**
   - Tablet sends `READY` to Hub.
   - Tablet → state `READY`. Status LED begins flashing.
   - Hub updates internal state, broadcasts updated `LOBBY_STATE`.
   - Players can also un-ready (lift cover back) → sends `UNREADY`, tablet → state `JOINED`.

2. **Hub checks start conditions** after every `READY`/`UNREADY`:
   - All connected players are `ready: true` **AND**
   - An NFC card is present (`nfc: true`) **AND**
   - At least 1 player is connected.

3. **When all conditions met → Hub sends `GAME_COUNTDOWN` (seconds: 5).**
   - Hub → state `COUNTDOWN`.
   - Tablets show countdown on command screen.
   - Hub speaker counts down: "5... 4... 3... 2... 1..."
   - All tablet LEDs pulse in unison.

4. **If a player un-readies during countdown** → Hub aborts countdown, returns to `LOBBY`, broadcasts updated `LOBBY_STATE`.

5. **If the NFC card is removed during countdown** → Hub aborts countdown, returns to `LOBBY`, broadcasts `NFC_REMOVED`.

6. **Countdown reaches 0 → Hub sends `GAME_START`.**
   - Hub → state `GAME_INTRO`.
   - All tablets → state `IN_GAME`.

### Message sequence

```
Tablet 1          Hub                   Tablet 2
  │                │                      │
  │── READY ─────►│                      │
  │                │── LOBBY_STATE ─────►│  (Tablet 1 now ready)
  │                │── LOBBY_STATE ──────────────►│
  │                │                      │
  │                │  [Tablet 2 readies]  │
  │                │◄── READY ────────────│
  │                │                      │
  │                │  All ready + NFC ✓   │
  │                │                      │
  │◄── GAME_COUNTDOWN ──│               │
  │                │── GAME_COUNTDOWN ──►│
  │                │                      │
  │  [5...4...3...2...1]                  │
  │                │                      │
  │◄── GAME_START ───────│               │
  │                │── GAME_START ───────►│
```

---

## Phase 4 — Game: Intro

**Duration:** 10–30 seconds (scenario-defined)

### Hub state: `GAME_INTRO`

### What happens

1. **Hub plays narrative audio** (V1 speaker, or V2 HDMI audio).
   - "Captain's log... we're approaching the asteroid belt..."
   - The intro text is defined in the scenario's phase 1 data.

2. **Hub sends `SCREEN_TEXT`** to each tablet with flavor text or role-specific setup instructions.
   - Style: `NARRATION`.
   - E.g., Navigator sees: "Plot a course through the debris field."
   - E.g., Engineer sees: "Engine core stable... for now."

3. **Hub may send initial `SCORE_UPDATE`** (health: 100, score: 0, streak: 0).

4. **When intro narration finishes → Hub sends `PHASE_CHANGE` (phase: `FRANTIC`).**
   - Hub → state `GAME_FRANTIC`.

### What tablets display

- Command screen: Narrative text (role-specific flavor).
- OLEDs: Scenario labels (already set from Phase 2).
- Status LED: Archetype color (steady).
- No commands to execute yet — this is scene-setting only.

### Message sequence

```
Hub                          Tablet 1              Tablet 2
 │                             │                     │
 │  [Playing intro audio]      │                     │
 │── SCREEN_TEXT ────────────►│                    │  (narration)
 │── SCREEN_TEXT ──────────────────────────────────►│  (narration)
 │── SCORE_UPDATE ───────────►│                    │  (health:100)
 │── SCORE_UPDATE ─────────────────────────────────►│
 │                             │                     │
 │  [Intro ends]               │                     │
 │── PHASE_CHANGE(FRANTIC) ──►│                    │
 │── PHASE_CHANGE(FRANTIC) ────────────────────────►│
```

---

## Phase 5 — Game: Frantic

**Duration:** 60–180 seconds (scenario-defined, counted down)

### Hub state: `GAME_FRANTIC`

This is the core gameplay loop. The Hub fires commands at tablets; players physically execute them.

### The Command Loop

The Hub runs an internal game tick (e.g., every 500ms–2s depending on difficulty) that:

1. **Draws a command** from the scenario's randomized command pool.
   - Selects a target player based on their archetype and available controls.
   - Selects a command type: `DIRECT`, `COOP`, or `CRISIS`.
   - Calculates timeout based on difficulty curve (gets shorter as game progresses).

2. **Sends the command to the target tablet:**

   - **Direct command → `COMMAND`** to the target tablet.
     - Tablet displays command on its screen: "Set thrust to 75%!"
     - Player physically moves the control.
     - Tablet sends `STATE` on control change.
     - When player is satisfied → presses Submit → tablet sends `SUBMIT`.
     - Hub evaluates: correct value within tolerance? → sends `CMD_RESULT`.

   - **Cooperative command → `COOP_COMMAND`** to a *different* tablet.
     - Tablet A's screen shows: "Tell the Engineer to close safety valve 2!"
     - Player A shouts the instruction to Player B.
     - Player B executes on their tablet → their tablet sends `STATE`/`SUBMIT`.
     - Hub correlates the action to the pending coop command → sends `CMD_RESULT` to both.

   - **Crisis → `CRISIS`** broadcast to all.
     - All tablets alarm: siren, vibration, screen flash.
     - All players press crisis buttons → each tablet sends `CRISIS_BTN`.
     - Hub waits for all (or enough) crisis button presses within timeout.
     - Hub sends `CMD_RESULT` to all with outcome.

3. **Hub updates game state** after each command resolution:
   - Adjusts health (failed/timed-out commands reduce health).
   - Adjusts score (successful commands add points; speed bonus for fast responses).
   - Updates streak counter.
   - Sends `SCORE_UPDATE` to all tablets after significant changes.

4. **Hub sends `HAPTIC`** as needed for feedback:
   - Short buzz + success tone on correct action.
   - Harsh buzz + fail tone on wrong action.
   - Ship damage rumble when health drops.

5. **Hub can send `CMD_CANCEL`** if a crisis overrides a pending command, or if the phase is ending.

6. **Hub can update OLEDs mid-game** via `OLED_LABELS` (e.g., narrative twist: "Main Thruster" → "FAILING — Reroute!").

### Difficulty Escalation

As the game progresses:
- Command timeouts shrink (15s → 8s → 5s).
- More cooperative and crisis commands enter the mix.
- Multiple commands may be active simultaneously on different tablets.
- The Hub may send commands to the same tablet faster than they can finish (pressure!).

### Health Check

Every game tick, the Hub checks:
- If `health <= 0` → immediate `GAME_OVER` (result: `LOSE`, reason: `HEALTH_ZERO`).
- If game timer expires → transition to wrap-up.

### Message sequence (typical 10-second window)

```
Hub                          Tablet 1 (Nav)        Tablet 2 (Eng)
 │                             │                     │
 │── COMMAND ────────────────►│                    │  "Rotate joystick to 45°"
 │                             │── STATE ──────────►│  (joystick moved)
 │                             │── SUBMIT ─────────►│  (confirmed)
 │── CMD_RESULT(SUCCESS) ────►│                    │
 │── HAPTIC(buzz+ding) ──────►│                    │
 │── SCORE_UPDATE ───────────►all                   │
 │                             │                     │
 │── COOP_COMMAND ───────────►│                    │  "Tell Eng: close valve 2!"
 │                             │  [Player 1 shouts]  │
 │                             │                     │── STATE ────────►│  (toggle flipped)
 │── CMD_RESULT(SUCCESS) ────►│                    │
 │── CMD_RESULT(SUCCESS) ──────────────────────────►│
 │                             │                     │
 │── CRISIS ─────────────────►all                    all
 │                             │── CRISIS_BTN ─────►│
 │                             │                     │── CRISIS_BTN ───►│
 │── CMD_RESULT(SUCCESS) ────►all                    all
 │                             │                     │
 │  [Timer expires]            │                     │
 │── PHASE_CHANGE(WRAPUP) ───►all                    all
```

---

## Phase 6 — Game: Wrap-Up

**Duration:** 15–30 seconds (scenario-defined)

### Hub state: `GAME_WRAPUP`

### What happens

1. **Hub sends `PHASE_CHANGE` (phase: `WRAPUP`).**
   - No more commands fire.
   - Tablets stop accepting input (or inputs are ignored by Hub).

2. **Hub plays wrap-up narration** (audio/HDMI).
   - "Great work, crew. We made it through the asteroid belt..."
   - May include educational content: "Did you know? The asteroid belt contains..."

3. **Hub sends `SCREEN_TEXT`** to tablets with debrief information.
   - Style: `NARRATION` or `SUCCESS`/`FAIL` depending on outcome.

4. **Phase ends → Hub transitions to `SCORE`.**

---

## Phase 7 — Score & Post-Game

**Duration:** Until host proceeds (button press, app action, or timeout)

### Hub state: `SCORE`

### What happens

1. **Hub sends `GAME_OVER`** with overall result, final score, health, and reason.

2. **Hub sends `SCORE_SUMMARY`** with per-player breakdown:
   - Commands correct / missed per player.
   - Average response time per player.
   - Crises survived.
   - Best streak.

3. **Tablets display score on command screen.**
   - Each tablet can highlight its own stats.
   - Status LEDs do a celebration pattern (win) or grim fade (lose).

4. **Hub plays result audio** ("Mission complete!" or "Mission failed...").

### What tablets display

- Command screen: Score summary, personal stats.
- Status LED: Celebration pattern or failure pattern.
- 7-segment: Player ID (unchanged).
- OLEDs: Can show final narrative labels or go blank.

### Message sequence

```
Hub                          Tablet 1              Tablet 2
 │                             │                     │
 │── GAME_OVER ──────────────►all                    all
 │── SCORE_SUMMARY ──────────►all                    all
 │                             │                     │
 │  [Score screen displayed]   │                     │
 │  [Waiting for host action]  │                     │
```

---

## Phase 8 — Return to Lobby / Power Down

### Option A: Play Again

1. Host presses Hub button (or acts via companion app).
2. Hub sends `RETURN_LOBBY` to all.
3. Hub → state `LOBBY`. All tablets → state `JOINED` (not ready).
4. If the same NFC card is still on the Hub, OLEDs remain labeled. Players just need to ready up again.
5. The next game run draws **fresh random commands** from the same scenario's pools.

### Option B: Switch Scenario

1. Player removes NFC card → Hub broadcasts `NFC_REMOVED`.
2. Hub → state `LOBBY`. OLEDs clear.
3. Player places a different NFC card → Phase 2 plays out again.

### Option C: Power Down

1. Host holds Hub button (long press) or uses companion app.
2. Hub sends `POWER_DOWN` to all tablets.
3. Tablets show "Shutting down...", LED fades, enter deep sleep or power off.
4. Hub powers off.

### Option D: Tablet Leaves

1. Player long-presses a button combo on their tablet (TBD).
2. Tablet sends `LEAVE` to Hub.
3. Hub removes player from peer table.
4. Hub broadcasts updated `LOBBY_STATE`.
5. Tablet → state `BOOT` (can re-join) or powers off.

---

## Edge Cases & Interrupts

### Tablet Disconnects Mid-Game

**Trigger:** Hub misses 3 consecutive heartbeats (1.5s of silence) from a tablet.

**Hub response:**
1. Marks player as disconnected internally.
2. Sends `KICK` (reason: `TIMEOUT`) to the tablet's last-known MAC (may not arrive).
3. Stops sending `COMMAND` / `COOP_COMMAND` to that player.
4. Any pending commands for that player auto-resolve as `TIMEOUT`.
5. Game **continues** with remaining players.
6. Hub announces disconnection via speaker: "Navigator offline!"
7. If ALL tablets disconnect → Hub transitions to `IDLE`.

**Tablet response (if it recovers):**
- Tablet notices it hasn't received anything from Hub.
- After 3s of Hub silence → reverts to `SEEKING` state, starts broadcasting `JOIN_REQ` again.
- Hub will reject with `JOIN_DENY` (reason: `GAME_ACTIVE`) until the current game ends.
- On `RETURN_LOBBY`, the tablet can re-join.

---

### NFC Card Removed Mid-Game

**Trigger:** Hub NFC reader detects card removal during `GAME_INTRO`, `GAME_FRANTIC`, or `GAME_WRAPUP`.

**Hub response:**
1. Broadcasts `NFC_REMOVED` (was_active: true).
2. Immediately sends `GAME_OVER` (result: `ABORT`, reason: `NFC_REMOVED`).
3. Hub → state `SCORE` (brief), then auto-transitions to `LOBBY` after 5 seconds.
4. Speaker: "Card removed — mission aborted."

**Design rationale:** The NFC card must remain on the Hub during play — same as a Tonie must stay on the box. Removing it is an intentional (or accidental) stop action. Quick transition back to lobby lets players re-place the card and try again without frustration.

---

### Low Battery During Play

**Trigger:** Tablet's heartbeat reports `bat <= 20`.

**Flow:**
1. Tablet sends `LOW_BAT` as a one-time alert (in addition to the `bat` field in regular heartbeats).
2. Hub receives and optionally broadcasts `LOW_BAT_WARN` to that tablet.
3. Tablet shows battery warning icon on command screen and/or flashes LED yellow briefly.
4. Hub speaker may announce: "Navigator's power is low!"
5. Game continues normally — low battery is a warning, not a stop condition.

**Critical battery (`bat <= 5`):**
- Tablet sends `LEAVE` (graceful) before entering deep sleep if possible.
- If it dies without `LEAVE`, Hub detects via missed heartbeats (same as disconnect).

---

### Late Join Attempt

**Trigger:** A new tablet broadcasts `JOIN_REQ` while a game is in progress.

**Hub response:**
- Sends `JOIN_DENY` (reason: `GAME_ACTIVE`).
- Tablet remains in `SEEKING` state, continues retrying every 1s.
- Once the Hub returns to `LOBBY` state, the next `JOIN_REQ` will be accepted normally.

---

### Duplicate Archetype Conflict

**Trigger:** A tablet sends `JOIN_REQ` with an archetype that another connected tablet already has.

**Hub response:**
- Sends `JOIN_DENY` (reason: `ARCH_TAKEN`).
- Tablet remains in `SEEKING` state.

**Resolution options:**
1. The other tablet with that archetype leaves → this one can join.
2. Host kicks the other tablet via companion app → frees the archetype.
3. This tablet gets physically swapped for a different archetype.

*Note: In a future firmware revision, we might allow duplicate archetypes with a "Player 1 Navigator / Player 2 Navigator" distinction, but for V1 each archetype may only appear once.*

---

### Hub Power Down / Abort

**Trigger:** Host long-presses Hub button, or uses companion app to shut down.

**Hub response:**
1. If game is active → sends `GAME_OVER` (result: `ABORT`, reason: `HOST_ABORT`).
2. Sends `POWER_DOWN` to all tablets.
3. Waits 500ms for messages to transmit.
4. Powers off.

**Tablet response:**
- Shows "Hub disconnected" on command screen.
- LED fades out.
- Tablet enters deep sleep after 5s of Hub silence (or powers off if user flips switch).

---

### Hardware Fault on Tablet

**Trigger:** A tablet detects an I2C failure, stuck control, display error, etc.

**Tablet response:**
1. Sends `ERROR` message to Hub with fault code, affected slot, and description.
2. Continues operating if possible (degraded mode — skip that OLED/control).
3. If fault is unrecoverable → sends `LEAVE` and reboots or shuts down.

**Hub response:**
1. Logs the error.
2. May announce: "Navigator reports a hardware fault."
3. Avoids sending commands that target the failed slot for the rest of the game.
4. If the tablet leaves, handles as standard disconnect.

---

### Multiple Hubs in Same Area

**Trigger:** Two or more Hubs are powered on and pairing in the same room (e.g., a tournament, a classroom, or adjacent family game nights).

**How isolation works (3 layers):**

1. **WiFi channel separation.** Each Hub auto-selects a channel (1, 6, or 11) at pairing time, picking the least congested. Two Hubs on different channels are invisible to each other at the radio layer. Tablets in `SEEKING` state rotate through all three channels, so they'll find any Hub within 3 seconds.

2. **ESP-NOW encryption.** Each Hub generates a unique 16-byte LMK (Local Master Key) per session. The key is shared with each tablet during `JOIN_ACK`. After that, all communication is encrypted. A tablet paired with Hub A cannot decrypt Hub B's messages — they're dropped silently by the ESP-NOW stack.

3. **Session ID filter.** Each Hub generates a 4-character session ID (e.g., `K7X2`) displayed on its 7-segment and announced by speaker. All messages carry a `sid` field. Even if layers 1 and 2 somehow fail, the application code drops messages with a mismatched `sid`.

**Player experience:**
- Tablets auto-pair to the first Hub that accepts them — no manual channel selection needed.
- If players need to ensure a tablet connects to a *specific* Hub (e.g., two Hubs side by side), they power on that Hub first and pair before powering on the second Hub. Or they check the session ID on the Hub's display.
- Once paired, cross-talk is impossible.

**See also:** [protocol.md — Multi-Hub Isolation](protocol.md#multi-hub-isolation) for the full technical specification.

---

## Timing Summary

| Event | Interval / Duration |
|---|---|
| `JOIN_REQ` retransmit | Every 1s |
| `HB` heartbeat | Every 500ms |
| Disconnect detection | 3 missed HBs = 1.5s |
| `LOBBY_STATE` broadcast | Every 2s |
| `SYNC_TIME` broadcast | Every 30s + once on join |
| Game countdown | 5 seconds |
| Command timeout (Easy) | 12–15 seconds |
| Command timeout (Medium) | 8–10 seconds |
| Command timeout (Hard) | 4–6 seconds |
| Crisis timeout | 3–5 seconds |
| Intro phase | 10–30 seconds |
| Frantic phase | 60–180 seconds |
| Wrap-up phase | 15–30 seconds |
| Score display | Until host action |
| NFC removal → lobby recovery | ~5 seconds auto |
| Tablet deep sleep after Hub loss | 5 seconds |
