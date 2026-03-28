# Tablet Archetypes — Control Loadouts & Role Definitions

> **Version:** 0.1.0 (Draft)
>
> This document defines every tablet archetype in the system. Each archetype is a unique hardware build with a fixed 5-control loadout. The Hub, companion app, and Mission Architect all reference these definitions.
>
> **See also:** [protocol.md](protocol.md) for message schemas and `ctrl` types, [game-loop.md](game-loop.md) for how commands flow during play.

---

## Table of Contents

- [Design Principles](#design-principles)
- [Base Tablet (Shared Across All Archetypes)](#base-tablet-shared-across-all-archetypes)
- [Archetype Summary](#archetype-summary)
- [Archetype Definitions](#archetype-definitions)
  - [1. Navigator](#1-navigator)
  - [2. Engineer](#2-engineer)
  - [3. Operator](#3-operator)
  - [4. Sentinel](#4-sentinel)
  - [5. Medic](#5-medic)
  - [6. Analyst](#6-analyst)
  - [7. Scout](#7-scout)
  - [8. Commander](#8-commander)
- [Narrative Label Examples](#narrative-label-examples)
- [Pin Budget Summary](#pin-budget-summary)
- [BOM Impact Comparison](#bom-impact-comparison)
- [Scaling & Future Archetypes](#scaling--future-archetypes)
- [Duplicate Archetype Policy](#duplicate-archetype-policy)

---

## Design Principles

### Complexity Distribution

Every archetype follows the same complexity curve:

| Slot | Complexity | Description |
|---|---|---|
| **Slot 1** | **High** | The archetype's signature control — analog, multi-step, or precision input. Unique across all 8 archetypes. |
| **Slot 2** | **Medium** | A dramatic or satisfying control — covered safety toggle or illuminated arcade button. |
| **Slots 3–5** | **Simple** | Toggle switches and momentary pushbuttons. Quick binary inputs. |

**Why this structure:**
- **Playability.** One complex control per tablet prevents overload. Players are doing frantic physical tasks under time pressure; cognitive complexity has to be metered.
- **Scenario design.** The Mission Architect can target the signature control for high-stakes commands and use the simple controls for rapid-fire binary decisions.
- **Manufacturing.** Slots 2–5 draw from a small shared parts pool (covered toggles, arcade buttons, standard toggles, pushbuttons). Only Slot 1 is unique per archetype.
- **Cost.** The signature control is the cost driver. Simple slots keep BOM low.

### Naming Convention

Archetype names are **deliberately generic** so they map naturally across any scenario theme:

| Archetype | Space | Pirate / Naval | Submarine | Fantasy |
|---|---|---|---|---|
| Navigator | Helmsman | Quartermaster | Helmsman | Pathfinder |
| Engineer | Systems Chief | Ship's Carpenter | Machinist | Artificer |
| Operator | Comms Officer | Signalman | Radio Operator | Herald |
| Sentinel | Security Chief | Master-at-Arms | Weapons Officer | Warden |
| Medic | Ship's Doctor | Surgeon | Corpsman | Healer |
| Analyst | Science Officer | Cartographer | Sonar Tech | Scholar |
| Scout | Recon Specialist | Lookout | Periscope Officer | Ranger |
| Commander | First Officer | Bosun | Executive Officer | Marshal |

The archetype name is the **base identity** (used in firmware, protocol, and identification). The scenario provides a **narrative role name** pushed to the tablet's command screen via `OLED_LABELS` and `SCREEN_TEXT`.

### Identification Feedback

Each archetype is assigned a unique LED color, speaker tone, and vibration pattern so players can identify their tablet at a glance across the table.

| # | Archetype | LED Color | RGB | Tone | Vibe Pattern |
|---|---|---|---|---|---|
| 1 | Navigator | Blue | `(0, 100, 255)` | Rising arpeggio | 2 short pulses |
| 2 | Engineer | Orange | `(255, 100, 0)` | Low power hum | 1 long pulse |
| 3 | Operator | Green | `(0, 200, 60)` | Radio chirp | 3 quick taps |
| 4 | Sentinel | Purple | `(140, 0, 255)` | Alert klaxon note | 2 long pulses |
| 5 | Medic | White | `(255, 255, 255)` | Soft chime | 1 short, 1 long |
| 6 | Analyst | Cyan | `(0, 200, 200)` | Data blip sequence | 4 rapid taps |
| 7 | Scout | Yellow | `(255, 200, 0)` | Sonar ping | 1 short pulse |
| 8 | Commander | Red | `(255, 0, 30)` | Authority horn blast | 3 long pulses |

> **Accessibility note:** Red/green colorblindness (deuteranopia) may make Engineer (orange) and Operator (green) harder to distinguish visually. The speaker tone and vibration pattern provide redundant identification channels. The 7-segment display also shows the unique player ID number.

---

## Base Tablet (Shared Across All Archetypes)

These components are present on **every** tablet regardless of archetype. They are not counted in the 5-slot loadout.

| Component | Interface | GPIO | Purpose |
|---|---|---|---|
| 1× Guarded Illuminated Pushbutton (safety cover + LED momentary) | Digital input + LED output | 2 | Crisis response; flip cover and press to ready-up |
| 1× Submit Button | Digital input | 1 | Lock in analog values |
| 1× 7-Segment Display (TM1637) | Custom 2-wire | 2 (CLK, DIO) | Player ID, connection status |
| 5× 1.3" I2C OLED (SSD1306/SH1106) | I2C via TCA9548A mux | 2 (shared SDA/SCL) | Per-slot narrative labels |
| 1× Command Screen (SPI TFT, size TBD) | SPI | 4 (MOSI, SCK, CS, DC) | Commands, cross-tablet directives |
| 1× Status RGB LED (WS2812 NeoPixel) | 1-wire data | 1 | Archetype color, alerts |
| 1× Speaker (piezo) | PWM | 1 | Tones, jingles, alerts |
| 1× Vibration Motor (coin, via MOSFET) | Digital output | 1 | Haptic feedback, identification |
| **Base total** | | **~14 GPIO** | |

---

## Archetype Summary

| # | ID | Name | Signature Control | Medium Control | Simple Controls | Add'l GPIO |
|---|---|---|---|---|---|---|
| 1 | `NAVIGATOR` | Navigator | Analog Joystick | Linear Slider (45mm) | Toggle, Toggle, Momentary Pushbutton | 8 |
| 2 | `ENGINEER` | Engineer | Linear Slider (60mm) | Illuminated Arcade Button | Toggle, Toggle, Toggle | 6 |
| 3 | `OPERATOR` | Operator | Rotary Encoder | Covered Safety Toggle | Toggle, Momentary, Momentary | 7 |
| 4 | `SENTINEL` | Sentinel | NFC/RFID Scanner (RC522) | 3-Position Rotary Switch | Toggle, Toggle, Momentary | 8 |
| 5 | `MEDIC` | Medic | Color-Match Dial | Rotary Encoder (small) | Toggle, Momentary, Momentary | 8 |
| 6 | `ANALYST` | Analyst | 4-Button Keypad | LED Wave Dial (small) | Toggle, Toggle, Momentary | 11 |
| 7 | `SCOUT` | Scout | LED Wave Dial | Covered Safety Toggle | Toggle, Toggle, Toggle | 6 |
| 8 | `COMMANDER` | Commander | Multi-Position Rotary Switch (6-pos) | Illuminated Arcade Button | Toggle, Momentary, Momentary | 6 |

Every archetype now has a T2-capable Slot 2 control. Each T2 action type appears on exactly two archetypes (one as Slot 1 signature, one as Slot 2 medium):
- `SET_SLIDER`: Engineer (sig) + Navigator (med)
- `SET_ENCODER`: Operator (sig) + Medic (med)
- `SET_ROTARY_SW`: Commander (sig) + Sentinel (med)
- `MATCH_WAVE`: Scout (sig) + Analyst (med)

---

## Archetype Definitions

### 1. Navigator

> *Direction, course-plotting, precision maneuvering.*

**Firmware ID:** `NAVIGATOR` · **LED:** Blue `(0, 100, 255)` · **Tone:** Rising arpeggio · **Vibe:** 2 short pulses

| Slot | Component | Interface | `ctrl` Type | Value Format | Notes |
|---|---|---|---|---|---|
| 1 | **Analog Joystick** (2-axis + click) | 2× ADC + 1 GPIO | `JOYSTICK` | `{"x": int8, "y": int8}` (−100 to 100) | Click is separate digital input; X/Y require Submit to lock in |
| 2 | **Linear Slider** (45mm slide pot) | 1 ADC | `SLIDER` | `uint8` (0–100, percent) | Requires Submit to lock in value. Shorter than Engineer's 60mm to differentiate feel. |
| 3 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 4 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 5 | Momentary Pushbutton | 1 GPIO | `BUTTON` | `bool` | |

**Additional GPIO:** 3 ADC + 5 digital = **8 pins**

**Gameplay flavor:** The Navigator handles steering and course corrections. The joystick is the star — precision aiming, course plotting, docking maneuvers. The slider controls throttle/speed — "set thrust to 70%." Toggles control auxiliary systems (thrusters, stabilizers). The pushbutton is a quick-confirm action.

---

### 2. Engineer

> *Power systems, machinery, throttle control.*

**Firmware ID:** `ENGINEER` · **LED:** Orange `(255, 100, 0)` · **Tone:** Low power hum · **Vibe:** 1 long pulse

| Slot | Component | Interface | `ctrl` Type | Value Format | Notes |
|---|---|---|---|---|---|
| 1 | **Linear Slider** (60mm slide pot) | 1 ADC | `SLIDER` | `uint8` (0–100, percent) | Requires Submit to lock in value |
| 2 | Illuminated Arcade Button | 2 GPIO (switch + LED) | `BUTTON` | `bool` | LED controlled by Hub via `HAPTIC` |
| 3 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 4 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 5 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |

**Additional GPIO:** 1 ADC + 5 digital = **6 pins**

**Gameplay flavor:** The Engineer manages raw power. Slider commands are "set thrust to 60%" or "reduce reactor to 25%." The arcade button is the big dramatic action — prime the engines, dump the core, fire the boilers. Toggles control subsystems (fuel lines, cooling, ventilation).

---

### 3. Operator

> *Signals, communication, fine-tuning.*

**Firmware ID:** `OPERATOR` · **LED:** Green `(0, 200, 60)` · **Tone:** Radio chirp · **Vibe:** 3 quick taps

| Slot | Component | Interface | `ctrl` Type | Value Format | Notes |
|---|---|---|---|---|---|
| 1 | **Rotary Encoder** (infinite scroll + click) | 2 GPIO (A, B) + 1 GPIO (btn) | `ENCODER` | `int16` (absolute position) | Click-push is a separate `BUTTON` event; scroll requires Submit |
| 2 | Covered Safety Toggle | 1 GPIO | `TOGGLE` | `bool` | |
| 3 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 4 | Momentary Pushbutton | 1 GPIO | `BUTTON` | `bool` | |
| 5 | Momentary Pushbutton | 1 GPIO | `BUTTON` | `bool` | |

**Additional GPIO:** 7 digital = **7 pins**

**Gameplay flavor:** The Operator tunes and adjusts. Rotary encoder commands are "tune frequency to 47" or "scroll to channel 12." The covered safety toggle is the broadcast override or emergency signal. Pushbuttons handle quick send/receive/confirm actions.

---

### 4. Sentinel

> *Security, defense, access control.*

**Firmware ID:** `SENTINEL` · **LED:** Purple `(140, 0, 255)` · **Tone:** Alert klaxon note · **Vibe:** 2 long pulses

| Slot | Component | Interface | `ctrl` Type | Value Format | Notes |
|---|---|---|---|---|---|
| 1 | **NFC/RFID Scanner** (RC522) | SPI (shared bus) + CS + IRQ | `NFC_SCAN` | `string` (scanned card UID) | Game packs include small NFC "item cards" (clearance badges, keys) |
| 2 | **3-Position Rotary Switch** | 1 ADC (resistor ladder) | `ROTARY_SW` | `uint8` (1–3, position) | 3 discrete positions; no Submit needed. Smaller than Commander's 6-pos. |
| 3 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 4 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 5 | Momentary Pushbutton | 1 GPIO | `BUTTON` | `bool` | |

**Additional GPIO:** 2 SPI-related + 1 ADC + 5 digital = **8 pins** (SPI bus shared with command screen)

**Gameplay flavor:** The Sentinel controls access and defense. NFC commands are "scan the RED clearance badge!" — the player must find the right physical card from the set included in the game pack and tap it on the scanner. The rotary switch selects alert levels or security modes (SAFE / CAUTION / LOCKDOWN). Toggles handle bulkhead doors, shield sectors, alarm systems.

**NFC Item Cards:** Each game pack can include a small set of themed NFC cards (e.g., colored clearance badges, key cards, artifact tokens). These are separate from the game-pack NFC card placed on the Hub. They add a physical "find the right card and scan it" mechanic unique to the Sentinel.

---

### 5. Medic

> *Health, diagnostics, chemical mixing.*

**Firmware ID:** `MEDIC` · **LED:** White `(255, 255, 255)` · **Tone:** Soft chime · **Vibe:** 1 short, 1 long

| Slot | Component | Interface | `ctrl` Type | Value Format | Notes |
|---|---|---|---|---|---|
| 1 | **Color-Match Dial** (pot + RGB LED) | 1 ADC + 1 GPIO (NeoPixel) | `COLOR_DIAL` | `[r, g, b]` | Pot sweeps through hues; RGB LED shows current color. Must match target, then Submit. |
| 2 | **Rotary Encoder** (small, EC11-style) | 2 GPIO (A, B) + 1 GPIO (btn) | `ENCODER` | `int16` (absolute position) | Scroll requires Submit; click is separate. Smaller knob than Operator's. |
| 3 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 4 | Momentary Pushbutton | 1 GPIO | `BUTTON` | `bool` | |
| 5 | Momentary Pushbutton | 1 GPIO | `BUTTON` | `bool` | |

**Additional GPIO:** 1 ADC + 7 digital = **8 pins**

**Gameplay flavor:** The Medic mixes and administers. Color-match commands are "mix the antidote to GREEN" — the player rotates the dial until the RGB LED matches. The rotary encoder controls dosage precision — "set dosage to 150" or "dial IV drip to 80." Pushbuttons are quick diagnostic confirms; toggles control life support and quarantine.

---

### 6. Analyst

> *Data entry, code sequences, research.*

**Firmware ID:** `ANALYST` · **LED:** Cyan `(0, 200, 200)` · **Tone:** Data blip sequence · **Vibe:** 4 rapid taps

| Slot | Component | Interface | `ctrl` Type | Value Format | Notes |
|---|---|---|---|---|---|
| 1 | **4-Button Keypad** (labeled 1–4) | 4 GPIO | `KEYPAD` | `string` (e.g., `"4231"`) | Player enters multi-digit codes. Submit locks in the sequence. |
| 2 | **LED Wave Dial** (small pot + 4-LED bar) | 1 ADC + 1 GPIO (NeoPixel data) | `WAVE_DIAL` | `uint8` (0–255 position) | Smaller than Scout's ring; 4-LED bar shows position. Must match target, then Submit. |
| 3 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 4 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 5 | Momentary Pushbutton | 1 GPIO | `BUTTON` | `bool` | |

**Additional GPIO:** 1 ADC + 10 digital = **11 pins**

**Gameplay flavor:** The Analyst handles data and codes. Keypad commands are "enter code 3-1-4-2" or "input sequence: 2-2-4-1." The wave dial tunes data frequencies or calibrates sensors — "tune signal to 180" or "set waveform to 60." Toggles manage data feeds and processing modes.

---

### 7. Scout

> *Reconnaissance, signal tracking, detection.*

**Firmware ID:** `SCOUT` · **LED:** Yellow `(255, 200, 0)` · **Tone:** Sonar ping · **Vibe:** 1 short pulse

| Slot | Component | Interface | `ctrl` Type | Value Format | Notes |
|---|---|---|---|---|---|
| 1 | **LED Wave Dial** (pot + NeoPixel ring) | 1 ADC + 1 GPIO (NeoPixel data) | `WAVE_DIAL` | `uint8` (0–255 position) | Potentiometer sweeps position; NeoPixel ring shows sweep point. Must match target, then Submit. |
| 2 | Covered Safety Toggle | 1 GPIO | `TOGGLE` | `bool` | |
| 3 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 4 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 5 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |

**Additional GPIO:** 1 ADC + 5 digital = **6 pins**

**Gameplay flavor:** The Scout tracks and detects. Wave dial commands are "tune scanner to position 180" or "lock tracking signal at 75%." The NeoPixel ring provides satisfying visual feedback as the player sweeps. The covered toggle is stealth mode / active scan override. Toggles control scan sectors and detection filters.

---

### 8. Commander

> *Authority, mode selection, critical decisions.*

**Firmware ID:** `COMMANDER` · **LED:** Red `(255, 0, 30)` · **Tone:** Authority horn blast · **Vibe:** 3 long pulses

| Slot | Component | Interface | `ctrl` Type | Value Format | Notes |
|---|---|---|---|---|---|
| 1 | **Multi-Position Rotary Switch** (6-pos) | 1 ADC (resistor ladder) | `ROTARY_SW` | `uint8` (1–6, position) | Chunky selector knob. Hub commands "set to position 4." No Submit needed — position is discrete. |
| 2 | Illuminated Arcade Button | 2 GPIO (switch + LED) | `BUTTON` | `bool` | |
| 3 | Toggle Switch | 1 GPIO | `TOGGLE` | `bool` | |
| 4 | Momentary Pushbutton | 1 GPIO | `BUTTON` | `bool` | |
| 5 | Momentary Pushbutton | 1 GPIO | `BUTTON` | `bool` | |

**Additional GPIO:** 1 ADC + 5 digital = **6 pins**

**Gameplay flavor:** The Commander selects modes and authorizes. Rotary switch commands are "set to BATTLE STATIONS" or "switch to position 3." The arcade button is the big authority action — launch, authorize, override. Toggles and pushbuttons handle quick tactical decisions (fire control, alert levels, comms channels).

---

## Narrative Label Examples

The same physical controls get relabeled per scenario via Hub-pushed `OLED_LABELS`. Here are examples across three themes:

### Navigator

| Slot | Control | Space Theme | Pirate Theme | Submarine Theme |
|---|---|---|---|---|
| 1 | Joystick | Helm Control | Ship's Wheel | Diving Planes |
| 2 | Slider | Thrust Level | Sail Trim | Speed Ahead |
| 3 | Toggle | Port Thruster | Port Sail | Left Rudder |
| 4 | Toggle | Starboard Thruster | Starboard Sail | Right Rudder |
| 5 | Pushbutton | Plot Course | Mark Position | Ping Sonar |

### Engineer

| Slot | Control | Space Theme | Pirate Theme | Submarine Theme |
|---|---|---|---|---|
| 1 | Slider | Reactor Output | Sail Hoist | Propulsion |
| 2 | Arcade Button | Engage FTL | Fire Cannons | Launch Torpedo |
| 3 | Toggle | Coolant Flow | Bilge Pump | Ballast Valve A |
| 4 | Toggle | Fuel Routing | Cargo Hatch | Ballast Valve B |
| 5 | Toggle | Ventilation | Gunport Doors | Air Recirculation |

### Sentinel

| Slot | Control | Space Theme | Pirate Theme | Submarine Theme |
|---|---|---|---|---|
| 1 | NFC Scanner | ID Badge Scanner | Captain's Seal | Access Card Reader |
| 2 | Rotary Switch | Alert Level | Battle Stance | Threat Level |
| 3 | Toggle | Shield Sector A | Armor Plating | Torpedo Tube 1 |
| 4 | Toggle | Shield Sector B | Boarding Nets | Torpedo Tube 2 |
| 5 | Pushbutton | Sound Alarm | Ring Bell | Collision Alarm |

### Medic

| Slot | Control | Space Theme | Pirate Theme | Submarine Theme |
|---|---|---|---|---|
| 1 | Color Dial | Mix Antidote | Brew Tonic | Mix O₂ Blend |
| 2 | Encoder | Dosage Dial | Tonic Strength | IV Drip Rate |
| 3 | Toggle | Medbay Power | Sickbay Lantern | Infirmary Light |
| 4 | Pushbutton | Run Diagnostic | Check Pulse | Read Vitals |
| 5 | Pushbutton | Request Supplies | Call for Rum | Request Blood Bank |

### Commander

| Slot | Control | Space Theme | Pirate Theme | Submarine Theme |
|---|---|---|---|---|
| 1 | Rotary Switch | Alert Level | Fleet Formation | Depth Setting |
| 2 | Arcade Button | Authorize Launch | Give the Order | Authorize Dive |
| 3 | Toggle | Comms Channel | Flag Signals | Silent Running |
| 4 | Pushbutton | All Hands | Bosun's Whistle | General Quarters |
| 5 | Pushbutton | Captain's Log | Ship's Log | Record Entry |

*(Operator, Analyst, and Scout follow the same pattern — the Hub relabels every slot per theme.)*

---

## Pin Budget Summary

| Component | GPIO Used | Notes |
|---|---|---|
| **Base tablet** | ~14 | Shared across all archetypes (see [Base Tablet](#base-tablet-shared-across-all-archetypes)) |
| **Archetype controls** | 6–9 | Varies by archetype (see summary table) |
| **Total per tablet** | **20–23** | |
| **ESP32-S3 available** | ~36 | Plenty of headroom |

### Per-Archetype Breakdown

| Archetype | ADC Pins | Digital GPIO | Total Added | Notes |
|---|---|---|---|---|
| Navigator | 3 (joystick X, Y + slider) | 5 | 8 | Joystick button is digital; slider = T2 throttle |
| Engineer | 1 (slider) | 5 | 6 | Arcade button LED is output |
| Operator | 0 | 7 | 7 | Encoder A, B, button = 3 |
| Sentinel | 1 (rotary switch ladder) | 7 | 8 | NFC shares SPI bus; 3-pos rotary via ADC |
| Medic | 1 (pot) | 7 | 8 | NeoPixel for RGB LED; encoder A, B, btn = 3 |
| Analyst | 1 (wave dial pot) | 10 | 11 | 4 keypad + wave dial (ADC + NeoPixel) + 2 toggles + 1 button |
| Scout | 1 (pot) | 5 | 6 | NeoPixel for LED ring |
| Commander | 1 (resistor ladder) | 5 | 6 | 6-pos switch via single ADC |

All archetypes fit comfortably within the ESP32-S3 GPIO budget.

---

## BOM Impact Comparison

Relative cost impact of each archetype's signature control versus the base tablet. Prices are rough estimates at 1,000+ unit volume.

| Archetype | Signature Component | Est. Unit Cost | Note |
|---|---|---|---|
| Navigator | Analog Joystick (PSP/thumbstick style) | ~$0.80 | Common, cheap |
| Engineer | 60mm Slide Potentiometer | ~$0.50 | Very common |
| Operator | Rotary Encoder (EC11-style) | ~$0.40 | Cheapest signature |
| Sentinel | RC522 NFC Module | ~$1.50 | Most expensive; adds NFC item-card gameplay |
| Medic | 10K Pot + WS2812 RGB LED | ~$0.60 | |
| Analyst | 4× tactile buttons + caps | ~$0.30 | Cheapest build |
| Scout | 10K Pot + NeoPixel Ring (8-LED) | ~$1.20 | Ring is the cost driver |
| Commander | 6-Position Rotary Switch | ~$0.70 | |

**Shared medium-tier components (per tablet):**

| Component | Est. Unit Cost | Notes |
|---|---|---|
| Covered Safety Toggle | ~$0.60 | Operator, Scout |
| Illuminated Arcade Button | ~$0.80 | Engineer, Commander |
| Linear Slider (45mm) | ~$0.40 | Navigator Slot 2 |
| 3-Position Rotary Switch | ~$0.50 | Sentinel Slot 2 |
| Rotary Encoder (EC11) | ~$0.40 | Medic Slot 2 |
| LED Wave Dial (4-LED bar) | ~$0.80 | Analyst Slot 2 |
| Standard Toggle Switch | ~$0.20 | |
| Momentary Pushbutton | ~$0.10 | |

**Archetype control BOM range:** ~$2.00–$4.50 per tablet on top of the base PCB cost.

---

## Scaling & Future Archetypes

### Current: 8 Archetypes = 8 Players Max

With 8 unique archetypes (one of each), the system supports the full 8-player cap. A **starter pack (4 tablets)** could ship with a curated selection:

| Pack | Included Archetypes | Rationale |
|---|---|---|
| **Core 4** | Navigator, Engineer, Operator, Sentinel | Covers steering, power, comms, defense — the essential crew |
| **Expansion 4** | Medic, Analyst, Scout, Commander | Adds depth and new mechanics (color matching, NFC items, data entry, authority) |

### Adding More Archetypes (V2+)

New archetypes can be added by:
1. Designing a new signature control not already in use.
2. Assigning a new firmware ID, LED color, tone, and vibe pattern.
3. Adding the `ctrl` type to [protocol.md](protocol.md).
4. Building scenario command maps that target the new control.

**Possible future signature controls:**
- Membrane keypad (full 0–9 + symbols)
- Touch strip / capacitive slider
- Pressure sensor (squeeze strength)
- Tilt/accelerometer (physical tilting)
- Multi-axis gimbal

**Constraint:** The Hub's command-dispatching logic scales linearly with archetype count. Scenarios need command maps for each archetype present, but can mark archetypes as "optional" — the Hub only dispatches commands to archetypes that actually connected.

---

## Duplicate Archetype Policy

### V1: One of Each

In V1 firmware, each archetype may appear **only once** per session. If a second Navigator tries to join, the Hub responds with `JOIN_DENY` (reason: `ARCH_TAKEN`).

**Rationale:** Simplifies command dispatching. "Navigator, set heading to 270" is unambiguous when there's only one Navigator.

### Future: Allow Duplicates

For larger events or team-based modes, future firmware could allow duplicate archetypes with disambiguation:
- Hub assigns sub-IDs: "Navigator 1" and "Navigator 2".
- Commands would target by player ID (already supported in protocol) rather than by archetype name alone.
- The scenario narrator would say "Player 3, set heading to 270!" using the player number instead of role name.

This requires no protocol changes — `COMMAND` already targets by `player_id`. Only the scenario's command voice lines and display text need to accommodate numbered players.
