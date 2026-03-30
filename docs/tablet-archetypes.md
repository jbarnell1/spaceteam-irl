# Tablet Archetypes — Control Loadouts & Role Definitions

> **Version:** 0.2.0 (Universal Base + Specialty Elements)
>
> This document defines every tablet archetype in the system. Each tablet shares a **universal control base** and carries **2 specialty elements** that define its archetype identity. The Hub, companion app, and Mission Architect all reference these definitions.

---

## Table of Contents

- [Design Philosophy](#design-philosophy)
- [Universal Base](#universal-base)
- [Specialty Element Pool](#specialty-element-pool)
- [Element Pairing Matrix](#element-pairing-matrix)
- [Archetype Definitions](#archetype-definitions)
  - [1. Navigator](#1-navigator)
  - [2. Engineer](#2-engineer)
  - [3. Operator](#3-operator)
  - [4. Sentinel](#4-sentinel)
  - [5. Medic](#5-medic)
  - [6. Analyst](#6-analyst)
  - [7. Scout](#7-scout)
  - [8. Commander](#8-commander)
- [Slot Naming & OLED Labels](#slot-naming--oled-labels)
- [Narrative Label Examples](#narrative-label-examples)
- [Statefulness & Pre-Flight](#statefulness--pre-flight)
- [Difficulty-Scaled Element Engagement](#difficulty-scaled-element-engagement)
- [Command Targeting Modes](#command-targeting-modes)
- [Pin Budget Summary](#pin-budget-summary)
- [BOM Impact](#bom-impact)
- [Scaling & Future Archetypes](#scaling--future-archetypes)
- [Duplicate Archetype Policy](#duplicate-archetype-policy)

---

## Design Philosophy

Every tablet shares a large **universal control base** — 3 toggle switches, 4 momentary buttons, a crisis button, and a submit button. This means every player always has plenty to do, regardless of archetype. The 7 universal slots alone generate a rich command space for easy/medium difficulty.

On top of the universal base, each tablet carries **2 specialty elements** drawn from a shared pool of 8 unique hardware elements. Each element appears on **exactly 2 archetypes** — no duplicates, no orphans. This creates:

- **OPEN commands:** Specialty actions that 2 different archetypes can race to complete (first responder wins).
- **Cross-tablet commands:** Display a specialty command on one player's screen for the other player who shares that element.
- **Difficulty scaling:** Easy games rely heavily on the universal base; harder games increasingly engage specialty elements.

The universal base ensures accessibility. The specialty elements create identity, chaos, and replayability.

---

## Universal Base

Every tablet has the same 10 physical controls in the universal base:

### Commandable Controls (7 slots)

| Slot Name | Control Type | Physical Form | Action Type |
|---|---|---|---|
| `toggle_1` | Toggle switch | **Bat** cap, color A | `SET_TOGGLE` |
| `toggle_2` | Toggle switch | **Rocker** cap, color B | `SET_TOGGLE` |
| `toggle_3` | Toggle switch | **Paddle** cap, color C | `SET_TOGGLE` |
| `button_1` | Momentary button | **Round**, red | `PRESS_BUTTON` |
| `button_2` | Momentary button | **Square**, blue | `PRESS_BUTTON` |
| `button_3` | Momentary button | **Oval**, yellow | `PRESS_BUTTON` |
| `button_4` | Momentary button | **Diamond**, green | `PRESS_BUTTON` |

All 3 toggles and 4 buttons use **different physical shapes and colors** so the Hub can command them by appearance: "Flip the bat switch!" or "Press the blue square!"

### System Controls (not scenario-commanded)

| Control | Physical Form | Purpose |
|---|---|---|
| **Crisis Button** | Guarded illuminated mushroom button | Crisis event response, ready-up |
| **Submit Button** | Distinct momentary (near command screen) | Lock in analog/specialty values |

---

## Specialty Element Pool

8 unique hardware elements, each appearing on exactly 2 archetypes:

| # | Element | Action Type | Tier | Description |
|---|---|---|---|---|
| 1 | **Joystick** | `SET_JOYSTICK` | T3 | 2-axis analog joystick (ADC X/Y + click). Value: `{x, y}` range -100 to 100. |
| 2 | **Slider / Fader** | `SET_SLIDER` | T2 | 45–60mm linear slide potentiometer. Value: 0–100 (percent). |
| 3 | **Barrel Jack Patch Bay** | `PLUG_JACK` | T2 | 3 barrel jack ports + 3 tethered wires (RED/1kΩ, BLUE/2.2kΩ, GREEN/4.7kΩ). Each port has a 10kΩ pull-down ADC pin for resistor identification. 34 valid states total. |
| 4 | **Rotary Encoder** | `SET_ENCODER` | T2 | Endless rotary encoder (A/B quadrature + click). Value: integer position. |
| 5 | **Number Pad** | `ENTER_CODE` | T3 | 4-button keypad (digits 1–4). Player enters a sequence and presses Submit. Value: string (e.g., "3142"). |
| 6 | **NFC Scanner** | `SCAN_NFC` | T3 | RC522 RFID/NFC reader (SPI). Player scans a tagged game badge/card. Value: card ID string. |
| 7 | **Rotary Switch** | `SET_ROTARY_SW` | T2 | 6-position selector switch (ADC resistor ladder). Value: 1–6. Simpler difficulties may use only positions 1–3. |
| 8 | **Color Dial** | `MATCH_COLOR` | T3 | Potentiometer + 2 addressable RGB LEDs (target LED + current LED). Player rotates to match the target color. Value: `[r, g, b]`. |

---

## Element Pairing Matrix

Each element appears on exactly 2 archetypes. No two archetypes share the same pair.

| Element | Archetype 1 | Archetype 2 |
|---|---|---|
| Joystick | **Navigator** (A) | **Scout** (A) |
| Slider / Fader | **Navigator** (B) | **Engineer** (A) |
| Barrel Jack Patch Bay | **Engineer** (B) | **Commander** (A) |
| Rotary Encoder | **Operator** (A) | **Medic** (B) |
| Number Pad | **Operator** (B) | **Analyst** (A) |
| NFC Scanner | **Sentinel** (A) | **Commander** (B) |
| Rotary Switch | **Sentinel** (B) | **Analyst** (B) |
| Color Dial | **Medic** (A) | **Scout** (B) |

**(A)** = `specialty_a` slot, **(B)** = `specialty_b` slot.

### Archetype Summary

| Archetype | Specialty A | Specialty B | Shared Elements With |
|---|---|---|---|
| **Navigator** | Joystick | Slider | Scout (Joy), Engineer (Slider) |
| **Engineer** | Slider | Barrel Jacks | Navigator (Slider), Commander (Jacks) |
| **Operator** | Rotary Encoder | Number Pad | Medic (Encoder), Analyst (NumPad) |
| **Sentinel** | NFC Scanner | Rotary Switch | Commander (NFC), Analyst (RotSwitch) |
| **Medic** | Color Dial | Rotary Encoder | Scout (Color), Operator (Encoder) |
| **Analyst** | Number Pad | Rotary Switch | Operator (NumPad), Sentinel (RotSwitch) |
| **Scout** | Joystick | Color Dial | Navigator (Joy), Medic (Color) |
| **Commander** | Barrel Jacks | NFC Scanner | Engineer (Jacks), Sentinel (NFC) |

---

## Archetype Definitions

All archetypes share the universal base (3 toggles, 4 buttons, crisis, submit). Only specialty elements differ.

### 1. Navigator

**Role:** Steering, flight control, thrust management.
**Specialty A:** Joystick — 2-axis analog (`SET_JOYSTICK`)
**Specialty B:** Slider / Fader — linear pot (`SET_SLIDER`)

The Navigator is the physical, kinetic role. The joystick feels like flying; the slider gives throttle control. Together with 3 toggles for thruster/system switches and 4 buttons for waypoints/confirmations, the Navigator has deep piloting gameplay.

**Typical commands:** "Hard to port!", "Thrust to 70%!", "Flip the bat switch!", "Press the red button!"

---

### 2. Engineer

**Role:** Power management, system routing, physical connections.
**Specialty A:** Slider / Fader — linear pot (`SET_SLIDER`)
**Specialty B:** Barrel Jack Patch Bay — 3 ports, 3 wires (`PLUG_JACK`)

The Engineer manages raw power levels (slider) and physically routes connections (plugging wires into ports). The barrel jacks are the most physically distinctive control in the game — pulling and plugging real cables under pressure is unforgettable.

**Typical commands:** "Power to maximum!", "Plug the RED wire into port 2!", "Flip the rocker switch!"

---

### 3. Operator

**Role:** Communications, frequency tuning, code entry.
**Specialty A:** Rotary Encoder — endless dial (`SET_ENCODER`)
**Specialty B:** Number Pad — 4-button keypad (`ENTER_CODE`)

The Operator tunes frequencies (encoder) and enters authorization codes (number pad). This archetype is the codebreaker — precise, methodical, and critical for cooperative commands where other players shout codes across the table.

**Typical commands:** "Tune to frequency 88!", "Enter code 3-1-4-2!", "Flip the paddle switch!"

---

### 4. Sentinel

**Role:** Security, access control, alert levels.
**Specialty A:** NFC Scanner — RFID reader (`SCAN_NFC`)
**Specialty B:** Rotary Switch — 6-position selector (`SET_ROTARY_SW`)

The Sentinel controls access (scanning badges) and sets alert/security levels (rotary switch). This is the gatekeeper role — physically scanning tagged cards under time pressure adds a unique, tactile urgency.

**Typical commands:** "Scan the ALPHA badge!", "Set alert to LOCKDOWN — position 3!", "Press the green diamond!"

---

### 5. Medic

**Role:** Medical compounds, dosage control, crew health.
**Specialty A:** Color Dial — pot + 2 RGB LEDs (`MATCH_COLOR`)
**Specialty B:** Rotary Encoder — endless dial (`SET_ENCODER`)

The Medic matches chemical compounds by color (color dial) and dials precise dosages (encoder). The color dial is visually spectacular — two LEDs showing target vs. current color, and the player rotates to match. High skill ceiling, very satisfying.

**Typical commands:** "Mix the BLUE stabilizer!", "Dosage to 150 — stat!", "Flip the bat switch!"

---

### 6. Analyst

**Role:** Data analysis, computations, signal processing.
**Specialty A:** Number Pad — 4-button keypad (`ENTER_CODE`)
**Specialty B:** Rotary Switch — 6-position selector (`SET_ROTARY_SW`)

The Analyst enters override codes (number pad) and selects analysis modes (rotary switch). This is the brainy role — under pressure, punching in codes correctly while selecting the right mode channel demands focus.

**Typical commands:** "Enter trajectory code 4-5-1-9!", "Set to analysis mode 4!", "Press the blue square!"

---

### 7. Scout

**Role:** Reconnaissance, sensor sweeps, stealth operations.
**Specialty A:** Joystick — 2-axis analog (`SET_JOYSTICK`)
**Specialty B:** Color Dial — pot + 2 RGB LEDs (`MATCH_COLOR`)

The Scout physically aims sensors (joystick) and matches signal colors for target identification (color dial). This archetype shares the joystick with Navigator and the color dial with Medic — creating OPEN command opportunities for both elements.

**Typical commands:** "Sweep sensors to bearing 120!", "Match the target signal — GREEN!", "Flip the paddle switch!"

---

### 8. Commander

**Role:** Authority, routing, overrides, mission-critical decisions.
**Specialty A:** Barrel Jack Patch Bay — 3 ports, 3 wires (`PLUG_JACK`)
**Specialty B:** NFC Scanner — RFID reader (`SCAN_NFC`)

The Commander physically routes ship systems (barrel jacks) and authorizes critical actions (NFC scan). This is the authority role — plugging in the right cables and scanning override badges under crisis pressure. Shares barrel jacks with Engineer and NFC with Sentinel.

**Typical commands:** "Plug the BLUE wire into port 1!", "Scan the OMEGA override badge!", "Press the red button!"

---

## Slot Naming & OLED Labels

Each tablet has **9 OLED displays** — one per commandable slot — showing narrative labels pushed by the Hub when a scenario loads.

| Slot | OLED Display Position | Universal / Specialty |
|---|---|---|
| `toggle_1` | Above bat toggle | Universal |
| `toggle_2` | Above rocker toggle | Universal |
| `toggle_3` | Above paddle toggle | Universal |
| `button_1` | Above round red button | Universal |
| `button_2` | Above square blue button | Universal |
| `button_3` | Above oval yellow button | Universal |
| `button_4` | Above diamond green button | Universal |
| `specialty_a` | Adjacent to specialty element A | Specialty |
| `specialty_b` | Adjacent to specialty element B | Specialty |

The Hub pushes 9 labels per tablet via `OLED_LABELS` when a scenario loads. Labels are max 16 characters. The same physical toggle becomes "Port Thruster" in one scenario and "East Gate" in another.

---

## Narrative Label Examples

### Station Omega (Space Theme)

| Archetype | toggle_1 | toggle_2 | toggle_3 | button_1 | button_2 | button_3 | button_4 | specialty_a | specialty_b |
|---|---|---|---|---|---|---|---|---|---|
| NAVIGATOR | Port Thruster | Stbd Thruster | Drift Brake | Mark Waypoint | Flare Launch | Sensor Ping | Dock Clamp | Helm Control | Thrust Lever |
| ENGINEER | Reactor | Coolant Valve | Fuel Dump | Emergency Vent | Purge Line | System Reset | Aux Power | Power Grid | Patch Bay |
| OPERATOR | Distress Beacon | Short-Range | Long-Range | Hail Vessel | Alert Broadcast | Jam Signal | Clear Channel | Frequency Dial | Auth Code |
| SENTINEL | Bulkhead Lock | Airlock Ctrl | Laser Grid | Alarm Bell | Badge Override | Deck Scan | Evac Signal | Access Badge | Alert Level |

### The Crimson Galleon (Pirate Theme)

| Archetype | toggle_1 | toggle_2 | toggle_3 | button_1 | button_2 | button_3 | button_4 | specialty_a | specialty_b |
|---|---|---|---|---|---|---|---|---|---|
| NAVIGATOR | Port Sail | Stbd Sail | Anchor | Bearing Mark | Signal Flare | Depth Ping | Grapple Hook | Helm | Sail Trim |
| ENGINEER | Bilge Pump | Cannon Port | Chain Hoist | Ram Brace | Keel Brace | Hull Patch | Powder Load | Steam Valve | Rigging Bay |

---

## Statefulness & Pre-Flight

### Stateful Controls

Some controls maintain persistent state between commands:

| Category | Controls | State Model |
|---|---|---|
| **Binary stateful** | Toggles, barrel jack ports | ON/OFF per switch/port. Hub tracks state; won't command "turn ON" if already ON. |
| **Continuous stateful** | Slider, encoder, color dial | Position value persists. Hub tracks approximate state for valid command generation. |
| **Discrete stateful** | Rotary switch | Position 1–6. Hub tracks current position. |
| **Momentary (stateless)** | Buttons, number pad, NFC scanner | Fire-and-forget. No state tracking needed. |

Scenario command pools **must** provide both ON and OFF variants for every toggle command, and multiple target values for continuous/discrete controls. The validator enforces this.

### Pre-Flight Initialization

At game start, before the first frantic phase, the Hub runs a **pre-flight sequence** that:

1. **Establishes known state.** Hub sends initialization commands ("Flip the bat switch ON!", "Set slider to 50%") that double as crew onboarding.
2. **Introduces controls narratively.** "Navigator, warm up your helm control. Set thrust to fifty percent." — blends tutorial with story.
3. **Syncs the Hub's state table.** Tablets report their actual state; Hub reconciles.
4. **Handles negligent players.** Hub encourages players who haven't completed pre-flight ("Look alive, Navigator!") but doesn't block others from proceeding.

The pre-flight phase is defined in each scenario's phase list as a `PREFLIGHT` phase with initialization commands per role.

---

## Difficulty-Scaled Element Engagement

The Hub varies how much it relies on specialty elements vs. the universal base depending on difficulty:

| Difficulty | Universal Base | Specialty Elements | Specialty Feedback |
|---|---|---|---|
| **Easy** | 80–90% of commands | 10–20% of commands | Element lights up + OLED hint shows exact target |
| **Medium** | 60–70% of commands | 30–40% of commands | OLED shows target value only (no element lighting) |
| **Hard** | 40–50% of commands | 50–60% of commands | Brief flash on element, then dark. Memory test. |
| **Extreme** | 30–40% of commands | 60–70% of commands | Cross-tablet: command appears on *another* player's screen |

**Exception — Joystick:** Skips "brief flash then dark" on Hard. Instead, Hard uses the same OLED-only feedback as Medium (shows target position + current position). The joystick's 2-axis nature makes pure memory impractical and unfun.

**Exception — Barrel Jacks on Extreme:** Does NOT cycle through all combinations. Instead uses single-wire placement: "Plug the GREEN wire into port 3!" — only 2 legitimate port options for simpler decision-making under extreme pressure.

---

## Command Targeting Modes

### TARGETED (Default)

Command targets a specific archetype. Only that player can execute it.

```json
{ "target_arch": "NAVIGATOR", "action": "SET_SLIDER", "slot": "specialty_b", ... }
```

### OPEN

Command targets `"ANY"` — any archetype that has the required element can respond. The first correct responder wins. All other tablets that were also eligible receive a **cooperative green flash** (not a "too late" dismissal — this feels positive, not punishing).

```json
{ "target": "ANY", "action": "SET_JOYSTICK", ... }
```

For `SET_JOYSTICK` OPEN commands, both Navigator and Scout can answer. The Hub auto-resolves the slot from each tablet's capability matrix. OPEN commands increase engagement on harder difficulties.

### COOP (Cross-Tablet)

Command appears on one player's screen but targets another player's controls. The display player must shout the instruction across the table.

```json
{ "display_on": "COMMANDER", "target_arch": "NAVIGATOR", "action": "SET_JOYSTICK", ... }
```

---

## Pin Budget Summary

### Per-Tablet GPIO Allocation (ESP32-S3-WROOM-1-N16R8)

| Subsystem | Pins | Notes |
|---|---|---|
| **I2C bus** (shared) | 2 | SDA + SCL for 9 OLEDs (muxed via TCA9548A) + command screen |
| **TCA9548A mux** | 1 | Reset pin (optional) |
| **Toggle switches ×3** | 3 | Digital input with pull-up |
| **Momentary buttons ×4** | 4 | Digital input with pull-up |
| **Crisis button** | 1 | Digital input |
| **Submit button** | 1 | Digital input |
| **Status RGB LED** | 1 | WS2812B data line |
| **Speaker** | 1 | PWM or I2S |
| **Vibration motor** | 1 | MOSFET-driven GPIO |
| **7-segment display** | 0 | On I2C bus (HT16K33) |
| **Battery ADC** | 1 | Voltage divider |
| **Subtotal (universal)** | **16** | |
| **Specialty A** | 1–4 | Varies by element (see below) |
| **Specialty B** | 1–4 | Varies by element |
| **Total** | **18–24** | Well within ESP32-S3 GPIO budget |

### Specialty Element Pin Costs

| Element | GPIO Pins | Notes |
|---|---|---|
| Joystick | 3 | X ADC + Y ADC + click digital |
| Slider | 1 | ADC |
| Barrel Jack Patch Bay | 3 | 3× ADC (one per port, resistor ID) |
| Rotary Encoder | 2 | A + B (click optional, shared with button) |
| Number Pad | 4 | 4× digital input (matrix or direct) |
| NFC Scanner | 4 | SPI (MOSI, MISO, SCK, CS) |
| Rotary Switch | 1 | ADC (resistor ladder) |
| Color Dial | 2 | ADC (pot) + data (WS2812B × 2 RGB LEDs) |

---

## BOM Impact

### Universal Base Cost (every tablet)

| Component | Qty | Unit Cost | Extended |
|---|---|---|---|
| Toggle switches (bat/rocker/paddle) | 3 | $0.35 | $1.05 |
| Momentary buttons (shaped, colored) | 4 | $0.25 | $1.00 |
| Crisis button (guarded illuminated) | 1 | $1.20 | $1.20 |
| Submit button | 1 | $0.15 | $0.15 |
| SSD1306 OLED 0.96" | 9 | $1.10 | $9.90 |
| TCA9548A I2C mux | 2 | $0.60 | $1.20 |
| Command screen (SSD1306 1.3" or ST7789 1.54") | 1 | $2.50 | $2.50 |
| ESP32-S3-WROOM-1 | 1 | $3.00 | $3.00 |
| **Universal subtotal** | | | **~$20.00** |

### Specialty Element Costs (2 per tablet)

| Element | Unit Cost | Notes |
|---|---|---|
| Joystick | $0.80 | PS2-style thumb joystick |
| Slider / Fader | $0.60 | 45mm linear pot |
| Barrel Jack Patch Bay | $1.50 | 3× panel-mount jacks + 3× tethered plugs + resistors |
| Rotary Encoder | $0.50 | EC11-style with knob |
| Number Pad | $0.80 | 4× tactile buttons + mounting |
| NFC Scanner | $1.80 | RC522 module (SPI) |
| Rotary Switch | $0.70 | 6-position + resistor ladder |
| Color Dial | $1.00 | Pot + 2× WS2812B LEDs |

Average specialty pair: ~$1.80. Total tablet COGS: ~$22–24 depending on archetype.

---

## Scaling & Future Archetypes

### Starter Pack (Core 4)

A minimum-viable product ships with 1 Hub + 4 tablets:

| Tablet | Specialty A | Specialty B |
|---|---|---|
| Navigator | Joystick | Slider |
| Engineer | Slider | Barrel Jacks |
| Operator | Rotary Encoder | Number Pad |
| Sentinel | NFC Scanner | Rotary Switch |

These 4 cover 6 of the 8 specialty elements (missing: Color Dial, Barrel Jacks duplicate coverage). All 4 have strong thematic identity and distinct physical feel.

### Expansion Pack (4 more)

| Tablet | Specialty A | Specialty B |
|---|---|---|
| Medic | Color Dial | Rotary Encoder |
| Analyst | Number Pad | Rotary Switch |
| Scout | Joystick | Color Dial |
| Commander | Barrel Jacks | NFC Scanner |

Completing the full 8 ensures every element appears on exactly 2 tablets, enabling the full OPEN command and cross-tablet mechanics.

### V2: New Elements

Future hardware revisions could add elements to the pool (e.g., a membrane pressure sensor, a tilt/accelerometer, a mini trackball). New elements would be paired onto a new pair of archetypes, or a "V2" variant of existing archetypes.

---

## Duplicate Archetype Policy

**V1: No duplicates.** The Hub rejects a `JOIN_REQ` if that archetype is already connected (`JOIN_DENY` reason: `ARCH_TAKEN`). Each archetype may appear at most once per session. Scenarios assume unique archetypes.

**Future:** For larger events or team-based modes, firmware could allow duplicate archetypes with disambiguation:
- Hub assigns sub-IDs: "Navigator 1" and "Navigator 2".
- Commands target by player ID (already supported in protocol) rather than by archetype alone.
- Narrator says "Player 3, set heading to 270!" using the player number instead of role name.

This requires no protocol changes — `COMMAND` already targets by `player_id`. Only scenario voice lines and display text need to accommodate numbered players.
