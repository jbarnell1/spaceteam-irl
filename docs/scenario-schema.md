# Scenario Schema & Mission Architect

> **Version:** 0.2.0 (Universal Base + Specialty Elements)
>
> This document defines the **scenario file format** — what a game pack actually contains — and the **Mission Architect** system that generates them. Every NFC card and companion-app game pack maps to one scenario file conforming to this schema.
>
> **See also:** [tablet-archetypes.md](tablet-archetypes.md) for control loadouts, [protocol.md](protocol.md) for message types, [game-loop.md](game-loop.md) for phase timing.

---

## Table of Contents

- [Command Capability Matrix](#command-capability-matrix)
  - [Slot Layout](#slot-layout)
  - [Action Types per Archetype](#action-types-per-archetype)
  - [Shared Actions (All Archetypes)](#shared-actions-all-archetypes)
  - [Command Complexity Tiers](#command-complexity-tiers)
  - [Statefulness](#statefulness)
- [Command Targeting Modes](#command-targeting-modes)
- [Scenario File Format](#scenario-file-format)
  - [Top-Level Structure](#top-level-structure)
  - [Metadata](#metadata)
  - [Role Map](#role-map)
  - [OLED Label Map](#oled-label-map)
  - [Command Pools](#command-pools)
    - [Direct Commands](#direct-commands)
    - [Cooperative Commands](#cooperative-commands)
    - [Open Commands](#open-commands)
  - [Crisis Events](#crisis-events)
  - [Phase Definitions](#phase-definitions)
    - [Pre-Flight Phase](#pre-flight-phase)
  - [Outcome Branches](#outcome-branches)
  - [Narrator Script](#narrator-script)
- [Outcome & Branching System](#outcome--branching-system)
  - [Performance Metrics](#performance-metrics)
  - [Branch Conditions](#branch-conditions)
  - [Outcome Tiers](#outcome-tiers)
  - [How the Hub Evaluates Outcomes](#how-the-hub-evaluates-outcomes)
- [Difficulty & Pacing](#difficulty--pacing)
  - [Difficulty Curves](#difficulty-curves)
  - [Adaptive Pacing](#adaptive-pacing)
  - [Narrator-Driven Pacing](#narrator-driven-pacing)
- [Replayability Mechanisms](#replayability-mechanisms)
- [Mission Architect (Content Engine)](#mission-architect-content-engine)
  - [Inputs](#inputs)
  - [Generation Pipeline](#generation-pipeline)
  - [Validation Rules](#validation-rules)
- [Example Scenario (Abridged)](#example-scenario-abridged)

---

## Command Capability Matrix

This is the master reference for what commands each archetype can physically execute. Every command in every scenario must map to an entry in this matrix.

### Slot Layout

Every tablet has **9 commandable slots** arranged in two groups:

**Universal Base (7 slots, identical on every tablet):**

| Slot | Control | Action Type | Value Format |
|---|---|---|---|
| `toggle_1` | Bat toggle switch | `SET_TOGGLE` | `bool` |
| `toggle_2` | Rocker toggle switch | `SET_TOGGLE` | `bool` |
| `toggle_3` | Paddle toggle switch | `SET_TOGGLE` | `bool` |
| `button_1` | Round red button | `PRESS_BUTTON` | `null` |
| `button_2` | Square blue button | `PRESS_BUTTON` | `null` |
| `button_3` | Oval yellow button | `PRESS_BUTTON` | `null` |
| `button_4` | Diamond green button | `PRESS_BUTTON` | `null` |

**Specialty Elements (2 slots, archetype-specific):**

| Slot | Varies by archetype |
|---|---|
| `specialty_a` | First specialty element |
| `specialty_b` | Second specialty element |

### Action Types per Archetype

Each row shows what action types are available on the specialty slots. All archetypes share the 7 universal slots (3× `SET_TOGGLE` + 4× `PRESS_BUTTON`).

| Archetype | `specialty_a` | `specialty_b` |
|---|---|---|
| **Navigator** | `SET_JOYSTICK` `{x,y}` | `SET_SLIDER` `0–100` |
| **Engineer** | `SET_SLIDER` `0–100` | `PLUG_JACK` `{port,wire}` |
| **Operator** | `SET_ENCODER` `int` | `ENTER_CODE` `"3142"` |
| **Sentinel** | `SET_TRIGGER` `0–100` | `SET_ROTARY_SW` `1–6` |
| **Medic** | `MATCH_COLOR` `[r,g,b]` | `SET_ENCODER` `int` |
| **Analyst** | `ENTER_CODE` `"3142"` | `SET_ROTARY_SW` `1–6` |
| **Scout** | `SET_JOYSTICK` `{x,y}` | `MATCH_COLOR` `[r,g,b]` |
| **Commander** | `PLUG_JACK` `{port,wire}` | `SCAN_NFC` `"uid"` |

**Element sharing:** Most specialty elements appear on 2 archetypes, enabling OPEN commands (either can answer) and cross-tablet commands. The Hall Trigger (Sentinel) and NFC Scanner (Commander) are each exclusive to one archetype.

| Element | Action Type | Archetypes |
|---|---|---|
| Joystick | `SET_JOYSTICK` | Navigator, Scout |
| Slider | `SET_SLIDER` | Navigator, Engineer |
| Barrel Jack Patch Bay | `PLUG_JACK` | Engineer, Commander |
| Rotary Encoder | `SET_ENCODER` | Operator, Medic |
| Number Pad | `ENTER_CODE` | Operator, Analyst |
| Hall Trigger | `SET_TRIGGER` | Sentinel |
| NFC Scanner | `SCAN_NFC` | Commander |
| Rotary Switch | `SET_ROTARY_SW` | Sentinel, Analyst |
| Color Dial | `MATCH_COLOR` | Medic, Scout |

### Shared Actions (All Archetypes)

These target **base tablet components** present on every archetype and are not scenario-commanded:

| Action | Component | Notes |
|---|---|---|
| `CRISIS_BTN` | Crisis Button (guarded illuminated pushbutton) | Crisis events — every player has one |
| `SUBMIT` | Submit Button | Locks in analog/specialty values — not a command action |

### Command Complexity Tiers

Commands are classified by how much cognitive/physical effort they require. The Hub uses this for pacing — it won't stack three high-complexity commands on the same player back-to-back.

| Tier | Description | Action Types | Avg. Execution Time |
|---|---|---|---|
| **T1 — Quick** | Binary flip or press. Instant. | `SET_TOGGLE`, `PRESS_BUTTON` | 1–2 seconds |
| **T2 — Standard** | Moderate precision or matching. | `SET_SLIDER`, `SET_ENCODER`, `SET_ROTARY_SW`, `PLUG_JACK`, `SET_TRIGGER` | 3–6 seconds |
| **T3 — Complex** | Multi-step or high precision. | `SET_JOYSTICK`, `MATCH_COLOR`, `ENTER_CODE`, `SCAN_NFC` | 5–12 seconds |

### Statefulness

Controls fall into two categories that affect command generation:

**Stateful controls** retain their physical position between commands. The Hub tracks state and ensures it only issues *valid* commands (e.g., won't say "flip switch ON" if already ON).

| Control | State Model | Pool Requirement |
|---|---|---|
| Toggles (`SET_TOGGLE`) | Binary ON/OFF | Must have both `true` and `false` variants per toggle |
| Barrel Jacks (`PLUG_JACK`) | Binary per port (wire in/out) | Multiple wire/port combinations |
| Slider (`SET_SLIDER`) | Continuous 0–100 | Multiple distinct target values |
| Rotary Encoder (`SET_ENCODER`) | Continuous integer | Multiple distinct target values |
| Rotary Switch (`SET_ROTARY_SW`) | Discrete 1–6 | Multiple position targets |
| Hall Trigger (`SET_TRIGGER`) | Continuous 0–100, spring-return | Multiple distinct target values (spring returns to 0 on release) |
| Color Dial (`MATCH_COLOR`) | Continuous [r,g,b] | Multiple distinct color targets |

**Momentary controls** are fire-and-forget. No state tracking needed:

| Control | Model |
|---|---|
| Buttons (`PRESS_BUTTON`) | Event — press and release |
| Number Pad (`ENTER_CODE`) | Sequence — resets after submit |
| NFC Scanner (`SCAN_NFC`) | Event — tap to scan |

The Hub tracks uncommanded state changes (a player flips a toggle without being told). No penalty for momentary presses. For stateful changes, the Hub updates its state table silently (natural consequences — it may affect future command generation). On harder difficulties, wrong submissions trigger active lockout (1–2 second input freeze on that control).

---

## Command Targeting Modes

Three modes govern who sees a command and who executes it:

### TARGETED (Direct)

Default mode. Command targets a specific archetype. Only that player sees and executes it.

```json
{
  "target_arch": "NAVIGATOR",
  "action": "SET_SLIDER",
  "slot": "specialty_b",
  "value": 75,
  ...
}
```

### OPEN

Command targets `"ANY"` — any archetype with the required action type can respond. Sent to all eligible tablets simultaneously. The **first correct responder wins**. Other eligible tablets receive a **cooperative green flash** (positive, not punishing).

```json
{
  "target": "ANY",
  "action": "SET_JOYSTICK",
  "value": {"x": -80, "y": 0},
  ...
}
```

For this command, both Navigator and Scout have a joystick. The Hub auto-resolves each tablet's slot from the capability matrix. OPEN commands increase engagement on harder difficulties and create emergent racing dynamics.

### COOP (Cross-Tablet)

Command appears on one player's screen but targets another player's controls. The display player must verbally shout the instruction.

```json
{
  "display_on": "COMMANDER",
  "target_arch": "NAVIGATOR",
  "action": "SET_JOYSTICK",
  "slot": "specialty_a",
  ...
}
```

---

## Scenario File Format

A scenario is a **JSON file** stored on the Hub's internal flash. It is the complete data package that powers one game session.

### Top-Level Structure

```json
{
  "schema_version": "1.0",
  "meta": { },
  "roles": { },
  "oled_labels": { },
  "command_pools": {
    "direct": [ ],
    "cooperative": [ ],
    "open": [ ]
  },
  "crises": [ ],
  "phases": [ ],
  "outcomes": { },
  "narrator": { }
}
```

### Metadata

```json
"meta": {
  "id": "STATION_OMEGA_01",
  "title": "Station Omega",
  "pack": "DEEP_SPACE_COLLECTION",
  "theme": "space",
  "subject": "teamwork",
  "age_rating": "8+",
  "difficulty": "medium",
  "player_count": { "min": 3, "max": 8 },
  "duration_sec": { "min": 840, "max": 900 },
  "adaptive_pacing": true,
  "version": "1.0.0",
  "author": "mission_architect"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique scenario identifier (UPPER_SNAKE) |
| `title` | `string` | Human-readable name |
| `pack` | `string` | Parent game pack ID |
| `theme` | `string` | Thematic setting (space, pirate, fantasy, etc.) |
| `subject` | `string` | Educational/thematic focus |
| `age_rating` | `string` | Target age group |
| `difficulty` | `string` | `easy`, `medium`, `hard`, or `extreme` — resolves all per-phase tuning from presets |
| `player_count` | `{min, max}` | Supported player range (1–8) |
| `duration_sec` | `{min, max}` | Expected total play time in seconds |
| `adaptive_pacing` | `bool` | Whether Hub adjusts command rate based on performance |
| `version` | `semver` | Schema version for this scenario |
| `author` | `string` | `mission_architect` or human author tag |

### Role Map

Maps archetype IDs to scenario-specific role names:

```json
"roles": {
  "NAVIGATOR":  "Helm Officer",
  "ENGINEER":   "Systems Engineer",
  "OPERATOR":   "Comms Officer",
  "SENTINEL":   "Security Chief",
  "MEDIC":      "Medical Officer",
  "ANALYST":    "Science Officer",
  "SCOUT":      "Recon Officer",
  "COMMANDER":  "Station Commander"
}
```

### OLED Label Map

Assigns narrative labels (max 16 chars) to each of a tablet's 9 commandable slots:

```json
"oled_labels": {
  "NAVIGATOR": [
    "Port Thruster", "Stbd Thruster", "Drift Brake",
    "Mark Waypoint", "Flare Launch", "Sensor Ping", "Dock Clamp",
    "Helm Control", "Thrust Lever"
  ],
  "ENGINEER": [
    "Reactor", "Coolant Valve", "Fuel Dump",
    "Emergency Vent", "Purge Line", "System Reset", "Aux Power",
    "Power Grid", "Patch Bay"
  ]
}
```

**Order:** `[toggle_1, toggle_2, toggle_3, button_1, button_2, button_3, button_4, specialty_a, specialty_b]`

Each label is max 16 characters.

### Command Pools

Commands are organized into three pools from which the Hub draws randomly during play:

#### Direct Commands

Targeted at a specific archetype. The player sees the command on their screen and executes it.

```json
{
  "id": "nav_hard_port",
  "target_arch": "NAVIGATOR",
  "action": "SET_JOYSTICK",
  "slot": "specialty_a",
  "tier": "T3",
  "label": "Hard to port — debris field!",
  "narrator_line": "Helm! Hard to port — debris field dead ahead!",
  "value": {"x": -80, "y": 0},
  "tolerance": {"x": 15, "y": 20},
  "timeout_ms": 8000
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | ✓ | Unique command identifier |
| `target_arch` | `string` | ✓ | Target archetype (must be in `ARCHETYPES`) |
| `action` | `string` | ✓ | Action type (must match archetype's slot capability) |
| `slot` | `string` | ✓ | Slot name: `toggle_1`–`toggle_3`, `button_1`–`button_4`, `specialty_a`, `specialty_b` |
| `tier` | `string` | ✓ | `T1`, `T2`, or `T3` |
| `label` | `string` | ✓ | Display text on command screen (max 40 chars) |
| `narrator_line` | `string` | ✓ | Audio text (max 200 chars) |
| `value` | varies | ✓ | Target value (format depends on action type) |
| `tolerance` | varies | | Acceptable deviation from target (analog/continuous controls) |
| `timeout_ms` | `int` | ✓ | Base timeout in milliseconds |

#### Cooperative Commands

Displayed on one player's screen, executed by another player. The display player must shout the instruction.

```json
{
  "id": "coop_cmd_tell_nav_port",
  "display_on": "COMMANDER",
  "target_arch": "NAVIGATOR",
  "action": "SET_JOYSTICK",
  "slot": "specialty_a",
  "tier": "T3",
  "label": "Tell Helm: hard to port!",
  "narrator_line": "Commander! Tell the Helm Officer — hard to port!",
  "value": {"x": -80, "y": 0},
  "tolerance": {"x": 15, "y": 20},
  "timeout_ms": 12000
}
```

Additional field: `display_on` — the archetype whose screen shows the command.

#### Open Commands

Target `"ANY"` — any archetype that has the required element on their tablet can respond. The Hub broadcasts to all eligible tablets; the first correct responder claims it. Others get a cooperative green flash.

```json
{
  "id": "open_joystick_evade",
  "target": "ANY",
  "action": "SET_JOYSTICK",
  "tier": "T3",
  "label": "Someone — hard evasive left!",
  "narrator_line": "Anyone with a flight stick — hard evasive left!",
  "value": {"x": -80, "y": 0},
  "tolerance": {"x": 15, "y": 20},
  "timeout_ms": 8000
}
```

| Field | Type | Description |
|---|---|---|
| `target` | `"ANY"` | Literal string `"ANY"` |
| `action` | `string` | Must be a specialty action (present on 2 archetypes) |

The Hub auto-resolves the slot for each eligible archetype from the capability matrix. OPEN commands should primarily target specialty elements (since all archetypes share universal controls, OPEN toggle/button commands would go to everyone — use CRISIS events for that).

### Crisis Events

Ship-wide emergencies that require multiple players to respond simultaneously:

```json
{
  "id": "crisis_hull_breach",
  "type": "CRISIS_ALL",
  "label": "HULL BREACH!",
  "narrator_line": "HULL BREACH! ALL HANDS — BRACE FOR DECOMPRESSION!",
  "required_count": "all",
  "timeout_ms": 5000,
  "penalty": "health_major"
}
```

**Crisis types:**

| Type | Description |
|---|---|
| `CRISIS_ALL` | All connected players must press crisis button |
| `CRISIS_THRESHOLD` | At least N players must press crisis button (`required_count`: integer) |
| `MULTI_ACTION` | Specific players do specific actions; rest press crisis button |

**MULTI_ACTION example:**

```json
{
  "id": "crisis_grav_surge",
  "type": "MULTI_ACTION",
  "label": "GRAVITY SURGE!",
  "narrator_line": "GRAVITY SURGE! Helm — pull up! Engineer — cut power! Everyone else — HOLD ON!",
  "actions": [
    { "target_arch": "NAVIGATOR", "action": "SET_JOYSTICK", "slot": "specialty_a", "value": {"x":0,"y":100}, "tolerance": {"x":25,"y":20} },
    { "target_arch": "ENGINEER",  "action": "SET_SLIDER",   "slot": "specialty_a", "value": 0, "tolerance": 10 },
    { "rest": "CRISIS_BTN" }
  ],
  "timeout_ms": 7000,
  "penalty": "health_major"
}
```

### Phase Definitions

The game progresses through a sequence of phases:

```
INTRO → PREFLIGHT → FRANTIC_1 → BRANCH_1 → FRANTIC_2 → BRANCH_2 → FRANTIC_3 → OUTCOME
```

#### Intro Phase

```json
{
  "id": "intro",
  "type": "NARRATION",
  "duration_sec": 60,
  "narrator_lines": [
    "Attention, station crew. This is Mission Control.",
    "A massive solar flare has struck the station."
  ]
}
```

#### Pre-Flight Phase

A scripted initialization sequence that establishes known control state and serves as crew onboarding. Runs after the intro narration, before the first frantic phase.

```json
{
  "id": "preflight",
  "type": "PREFLIGHT",
  "duration_sec": 45,
  "narrator_intro": "All crew, pre-flight check. Report your stations.",
  "init_commands": {
    "NAVIGATOR": [
      { "slot": "toggle_1", "action": "SET_TOGGLE", "value": true, "label": "Port thruster — ON!", "narrator_line": "Navigator, engage the port thruster." },
      { "slot": "specialty_b", "action": "SET_SLIDER", "value": 50, "label": "Set thrust to fifty percent.", "narrator_line": "Navigator, set thrust to fifty percent." }
    ],
    "ENGINEER": [
      { "slot": "toggle_1", "action": "SET_TOGGLE", "value": false, "label": "Reactor — OFF for now.", "narrator_line": "Engineer, confirm reactor is offline." },
      { "slot": "specialty_a", "action": "SET_SLIDER", "value": 0, "label": "Power grid to zero.", "narrator_line": "Engineer, power grid to zero — standby." }
    ]
  },
  "timeout_per_command_ms": 15000,
  "encourage_line": "Look alive, {role}! We need you at your station."
}
```

**Pre-flight behavior:**
- Hub issues init commands one archetype at a time (or in small batches).
- Tablets report their actual control state; Hub reconciles its state table.
- If a player doesn't complete their pre-flight within the timeout, Hub plays the `encourage_line` but does **not** block other players from proceeding.
- Serves as a tutorial for new players ("flip the bat switch" teaches them which switch is which).
- Sets all stateful controls to a known starting position for the Hub's state tracker.

#### Frantic Phase

The core gameplay — commands fire at increasing pace:

```json
{
  "id": "frantic_1",
  "type": "FRANTIC",
  "duration_sec": 240,
  "difficulty": {
    "commands_per_min": { "start": 3, "end": 5 },
    "coop_ratio": 0.15,
    "open_ratio": 0.05,
    "crisis_chance_per_30s": 0.10,
    "timeout_multiplier": 1.3
  },
  "pools": ["direct", "cooperative", "open"],
  "crises": ["crisis_hull_breach", "crisis_solar_flare"],
  "narrator_lines_ambient": [
    "Focus on restoring core systems.",
    "Station integrity is holding... for now."
  ]
}
```

New field: `open_ratio` — fraction of commands drawn from the OPEN pool. Combined with `coop_ratio`, the remainder is direct commands.

#### Branch Phase

Evaluates performance and chooses next path:

```json
{
  "id": "branch_1",
  "type": "BRANCH",
  "evaluate": "frantic_1",
  "threshold": 0.55,
  "win": {
    "narrator_lines": ["Impressive work. Core systems are back online."],
    "next_phase": "frantic_2_W"
  },
  "lose": {
    "narrator_lines": ["Systems are still critical."],
    "next_phase": "frantic_2_L"
  }
}
```

The 3-branch structure creates 8 possible paths (WWW through LLL), each with its own frantic phase variant and outcome.

### Outcome Branches

```json
"outcomes": {
  "WWW": { "tier": "TRIUMPH",  "title": "Perfect Escape",   "narrator_lines": ["..."] },
  "WWL": { "tier": "SUCCESS",  "title": "Narrow Escape",    "narrator_lines": ["..."] },
  "WLW": { "tier": "SUCCESS",  "title": "Recovery Arc",     "narrator_lines": ["..."] },
  "WLL": { "tier": "SURVIVE",  "title": "Limping Home",     "narrator_lines": ["..."] },
  "LWW": { "tier": "SUCCESS",  "title": "Against the Odds", "narrator_lines": ["..."] },
  "LWL": { "tier": "SURVIVE",  "title": "By the Skin",      "narrator_lines": ["..."] },
  "LLW": { "tier": "SURVIVE",  "title": "Last Gasp",        "narrator_lines": ["..."] },
  "LLL": { "tier": "FAILURE",  "title": "Station Lost",     "narrator_lines": ["..."] }
}
```

**Outcome tiers (5 levels):**

| Tier | Description | Path Example |
|---|---|---|
| `TRIUMPH` | Flawless victory — best possible ending | WWW |
| `SUCCESS` | Solid win with some setbacks | WWL, WLW, LWW |
| `SURVIVE` | Barely made it — bittersweet | WLL, LWL, LLW |
| `FAILURE` | Mission failed — something was lost | LLL |
| `DISASTER` | Catastrophic loss (reserved for extreme difficulty) | N/A normally |

#### Sub-Analysis

Each outcome can include a `sub_analysis` block for finer grading within a tier:

```json
"WWW": {
  "tier": "TRIUMPH",
  "title": "Perfect Escape",
  "sub_analysis": {
    "health >= 80": { "badge": "FLAWLESS", "narrator_line": "Not a scratch on the hull." },
    "health >= 50": { "badge": "SOLID",    "narrator_line": "Some dents, but she held." },
    "default":      { "badge": "SCRAPPY",  "narrator_line": "We made it, barely." }
  },
  "narrator_lines": ["..."]
}
```

### Narrator Script

```json
"narrator": {
  "voice_id": "narrator_commander_01",
  "intro_lines": ["..."],
  "ambient_pool": ["..."],
  "crisis_lines": { "crisis_id": "line" },
  "outro_lines": { "TRIUMPH": ["..."], "FAILURE": ["..."] }
}
```

---

## Outcome & Branching System

### Performance Metrics

The Hub continuously tracks during each frantic phase:

| Metric | Weight | Description |
|---|---|---|
| `cmd_success_rate` | 0.40 | Ratio of correctly completed commands |
| `avg_response_ms` | 0.25 | Average time from command issue to correct response |
| `crisis_survival_rate` | 0.20 | Crises survived vs. total crises encountered |
| `health_retained` | 0.15 | Remaining health as fraction of starting health |

### Branch Conditions

At each branch point, the Hub computes a **weighted performance score** (0.0–1.0) for the preceding frantic phase. If the score meets or exceeds the **threshold**, the crew "wins" that branch.

**Default thresholds by difficulty:**

| Difficulty | Threshold |
|---|---|
| Easy | 0.45 |
| Medium | 0.55 |
| Hard | 0.60 |
| Extreme | 0.65 |

Scenarios can override thresholds per branch point.

### How the Hub Evaluates Outcomes

1. **Frantic phase ends** (timer expires or health hits 0).
2. Hub computes weighted score for that phase.
3. Compares against threshold → **Win** or **Lose**.
4. Appends `W` or `L` to the running path string (e.g., `"W"` → `"WL"` → `"WLW"`).
5. After the third branch, the 3-letter path (e.g., `"WLW"`) selects the final outcome.
6. Hub plays the matching outcome narration and sends scores.

---

## Difficulty & Pacing

### Difficulty Curves

Scenarios declare `meta.difficulty` (easy/medium/hard/extreme). All per-phase tuning resolves automatically from shared presets in `difficulty_presets.py`. Scenarios can override individual phase difficulty blocks if precise control is needed.

**Key parameters per frantic phase:**

| Parameter | Description |
|---|---|
| `commands_per_min` | `{start, end}` — ramps across the phase |
| `coop_ratio` | Fraction of commands from co-op pool (0.0–1.0) |
| `open_ratio` | Fraction of commands from OPEN pool (0.0–1.0) |
| `crisis_chance_per_30s` | Probability of a crisis event per 30-second window |
| `timeout_multiplier` | Multiplier on base command timeouts (>1.0 = more time) |
| `duration_sec` | Phase length in seconds |

### Adaptive Pacing

When `meta.adaptive_pacing` is true, the Hub dynamically adjusts:
- If crew is struggling (low success rate) → slow command rate by up to 20%.
- If crew is crushing it (high success rate, fast responses) → increase rate by up to 15%.
- Never exceeds difficulty level bounds (easy never reaches medium's peak pace).

### Narrator-Driven Pacing

- **Easy difficulty:** More narrator commands — the narrator explicitly tells players what to do and when. Frequent ambient lines provide breathing room. Narrative sections naturally slow the command rate.
- **Medium difficulty:** Balanced. Narrator intros and outros, with moderate ambient lines during frantic phases.
- **Hard/Extreme difficulty:** Minimal narrator interruption during frantic phases. Forces concurrent work + narrator listening. At extreme, commands may arrive during narrator lines — players must multitask.

---

## Replayability Mechanisms

Each game run is different because:

1. **Random pool draws.** The Hub randomly selects commands from the pools each time. Two runs of the same scenario at the same difficulty will issue different command sequences.
2. **8 outcome paths.** The branching system means run outcomes depend on real-time performance.
3. **Player count adaptation.** Commands scale to connected players. A 3-player run focuses commands on 3 archetypes; an 8-player run distributes across all.
4. **OPEN command racing.** Two eligible archetypes race to complete OPEN commands — the winner is unpredictable.
5. **Adaptive pacing.** The Hub adjusts to the crew's skill, so even repeated runs feel appropriately challenging.

---

## Mission Architect (Content Engine)

The Mission Architect is an LLM-powered pipeline that generates scenario JSON files from high-level creative briefs.

### Inputs

| Input | Description |
|---|---|
| Theme brief | "Space station rescue", "Pirate treasure hunt", "Dragon siege defense" |
| Target difficulty | easy / medium / hard / extreme |
| Player count range | e.g., 3–8, or 1–2 for duo scenarios |
| Subject tags | "teamwork", "geography", "math", "history" |
| Duration target | e.g., 15 minutes |

### Generation Pipeline

1. **Narrative scaffold:** Generate intro/outro/branch narration for the theme.
2. **Role mapping:** Assign thematic role names to each archetype.
3. **OLED labels:** Generate 9 labels per archetype, themed to scenario. Max 16 chars.
4. **Command pools:** Generate direct, cooperative, and open commands covering all archetypes and tiers, respecting the capability matrix.
5. **Crises:** Generate crisis events themed to the scenario.
6. **Pre-flight:** Generate initialization commands for the pre-flight sequence.
7. **Phase timing:** Set phase durations or rely on difficulty presets.
8. **Outcomes:** Write 8 branched endings.
9. **Validate:** Pass through `missions/validate/` pipeline.
10. **Audio:** Generate narrator TTS audio for each line; store on SPI NAND.

### Validation Rules

The validation pipeline (`missions/validate/`) enforces:

1. **Capability compliance:** Every command's `action`+`slot` must match the target archetype's capability matrix entry.
2. **Pool coverage:** Each archetype must have ≥5 direct commands and ≥2 cooperative commands.
3. **Tier balance:** Each archetype's commands must span T1, T2, and T3 tiers.
4. **Statefulness:** Binary stateful commands (toggles) must have both ON and OFF variants in the pool for each toggle slot.
5. **OLED labels:** Exactly 9 labels per archetype, max 16 chars each.
6. **Label lengths:** Command labels ≤40 chars, narrator lines ≤200 chars.
7. **Unique IDs:** All command IDs, crisis IDs, and phase IDs must be unique.
8. **Crisis requirements:** Minimum 2 crisis events per scenario. Valid types only.
9. **Phase structure:** Must include intro, all 7 frantic phase IDs, all branch phases, and all 8 outcomes.
10. **Outcome coverage:** All 8 paths (WWW–LLL) must have matching outcomes with valid tiers.
11. **OPEN command validity:** OPEN commands must target specialty actions (present on exactly 2 archetypes). Universal actions are not valid OPEN targets.
12. **Pre-flight coverage:** If a PREFLIGHT phase exists, it should include init commands for stateful controls.

---

## Example Scenario (Abridged)

```json
{
  "schema_version": "1.0",
  "meta": {
    "id": "STATION_OMEGA_01",
    "title": "Station Omega",
    "pack": "DEEP_SPACE_COLLECTION",
    "theme": "space",
    "subject": "teamwork",
    "age_rating": "8+",
    "difficulty": "medium",
    "player_count": { "min": 3, "max": 8 },
    "duration_sec": { "min": 840, "max": 900 },
    "adaptive_pacing": true,
    "version": "1.0.0",
    "author": "mission_architect"
  },

  "roles": {
    "NAVIGATOR": "Helm Officer",
    "ENGINEER": "Systems Engineer"
  },

  "oled_labels": {
    "NAVIGATOR": [
      "Port Thruster", "Stbd Thruster", "Drift Brake",
      "Mark Waypoint", "Flare Launch", "Sensor Ping", "Dock Clamp",
      "Helm Control", "Thrust Lever"
    ]
  },

  "command_pools": {
    "direct": [
      {
        "id": "nav_hard_port",
        "target_arch": "NAVIGATOR",
        "action": "SET_JOYSTICK",
        "slot": "specialty_a",
        "tier": "T3",
        "label": "Hard to port — debris field!",
        "narrator_line": "Helm! Hard to port — debris field dead ahead!",
        "value": {"x": -80, "y": 0},
        "tolerance": {"x": 15, "y": 20},
        "timeout_ms": 8000
      },
      {
        "id": "nav_port_on",
        "target_arch": "NAVIGATOR",
        "action": "SET_TOGGLE",
        "slot": "toggle_1",
        "tier": "T1",
        "label": "Port thruster — FIRE!",
        "narrator_line": "Fire the port thruster!",
        "value": true,
        "timeout_ms": 3000
      }
    ],
    "cooperative": [
      {
        "id": "coop_cmd_tell_nav_port",
        "display_on": "COMMANDER",
        "target_arch": "NAVIGATOR",
        "action": "SET_JOYSTICK",
        "slot": "specialty_a",
        "tier": "T3",
        "label": "Tell Helm: hard to port!",
        "narrator_line": "Commander! Tell the Helm Officer — hard to port!",
        "value": {"x": -80, "y": 0},
        "tolerance": {"x": 15, "y": 20},
        "timeout_ms": 12000
      }
    ],
    "open": [
      {
        "id": "open_joystick_evade",
        "target": "ANY",
        "action": "SET_JOYSTICK",
        "tier": "T3",
        "label": "Someone — hard evasive left!",
        "narrator_line": "Anyone with a flight stick — hard evasive left!",
        "value": {"x": -80, "y": 0},
        "tolerance": {"x": 15, "y": 20},
        "timeout_ms": 8000
      }
    ]
  },

  "crises": [
    {
      "id": "crisis_hull_breach",
      "type": "CRISIS_ALL",
      "label": "HULL BREACH!",
      "narrator_line": "HULL BREACH! ALL HANDS — BRACE FOR DECOMPRESSION!",
      "required_count": "all",
      "timeout_ms": 5000,
      "penalty": "health_major"
    }
  ],

  "phases": [
    { "id": "intro", "type": "NARRATION", "duration_sec": 60, "narrator_lines": ["..."] },
    { "id": "preflight", "type": "PREFLIGHT", "duration_sec": 45, "narrator_intro": "All crew, systems check.", "init_commands": {} },
    { "id": "frantic_1", "type": "FRANTIC", "pools": ["direct", "cooperative", "open"], "crises": ["crisis_hull_breach"] },
    { "id": "branch_1", "type": "BRANCH", "evaluate": "frantic_1" },
    { "id": "frantic_2_W", "type": "FRANTIC", "...": "..." },
    { "id": "frantic_2_L", "type": "FRANTIC", "...": "..." },
    { "id": "branch_2", "type": "BRANCH", "evaluate": "current" },
    { "id": "frantic_3_WW", "type": "FRANTIC", "...": "..." },
    { "id": "frantic_3_WL", "type": "FRANTIC", "...": "..." },
    { "id": "frantic_3_LW", "type": "FRANTIC", "...": "..." },
    { "id": "frantic_3_LL", "type": "FRANTIC", "...": "..." }
  ],

  "outcomes": {
    "WWW": { "tier": "TRIUMPH", "title": "Perfect Escape", "narrator_lines": ["..."] },
    "LLL": { "tier": "FAILURE", "title": "Station Lost",   "narrator_lines": ["..."] }
  }
}
```

This is an abridged example. A full scenario includes all 8 archetypes in `roles`, `oled_labels`, complete command pools, multiple crises, full phase definitions, and all 8 outcomes.
