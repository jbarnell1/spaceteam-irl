# Scenario Schema & Mission Architect

> **Version:** 0.1.0 (Draft)
>
> This document defines the **scenario file format** — what a game pack actually contains — and the **Mission Architect** system that generates them. Every NFC card and companion-app game pack maps to one scenario file conforming to this schema.
>
> **See also:** [tablet-archetypes.md](tablet-archetypes.md) for control loadouts, [protocol.md](protocol.md) for message types, [game-loop.md](game-loop.md) for phase timing.

---

## Table of Contents

- [Command Capability Matrix](#command-capability-matrix)
  - [Action Types per Archetype](#action-types-per-archetype)
  - [Shared Actions (All Archetypes)](#shared-actions-all-archetypes)
  - [Command Complexity Tiers](#command-complexity-tiers)
- [Scenario File Format](#scenario-file-format)
  - [Top-Level Structure](#top-level-structure)
  - [Metadata](#metadata)
  - [Role Map](#role-map)
  - [OLED Label Map](#oled-label-map)
  - [Command Pools](#command-pools)
  - [Crisis Events](#crisis-events)
  - [Phase Definitions](#phase-definitions)
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
- [Replayability Mechanisms](#replayability-mechanisms)
- [Mission Architect (Content Engine)](#mission-architect-content-engine)
  - [Inputs](#inputs)
  - [Generation Pipeline](#generation-pipeline)
  - [Validation Rules](#validation-rules)
- [Example Scenario (Abridged)](#example-scenario-abridged)

---

## Command Capability Matrix

This is the master reference for what commands each archetype can physically execute. Every command in every scenario must map to an entry in this matrix.

### Action Types per Archetype

Each row is an archetype. Each column is a protocol action type. The cell shows which **slot** handles that action and the **value format** expected.

| Archetype | `SET_JOYSTICK` | `SET_SLIDER` | `SET_ENCODER` | `SCAN_NFC` | `MATCH_COLOR` | `ENTER_CODE` | `MATCH_WAVE` | `SET_ROTARY_SW` | `SET_TOGGLE` | `PRESS_BUTTON` |
|---|---|---|---|---|---|---|---|---|---|---|
| **Navigator** | Slot 1 `{x,y}` | Slot 2 `0–100` | — | — | — | — | — | — | Slots 3–4 | Slot 5 |
| **Engineer** | — | Slot 1 `0–100` | — | — | — | — | — | — | Slots 3–5 | Slot 2 |
| **Operator** | — | — | Slot 1 `int16` | — | — | — | — | — | Slots 2–3 | Slots 4–5 |
| **Sentinel** | — | — | — | Slot 1 `uid` | — | — | — | Slot 2 `1–3` | Slots 3–4 | Slot 5 |
| **Medic** | — | — | Slot 2 `int16` | — | Slot 1 `[r,g,b]` | — | — | — | Slot 3 | Slots 4–5 |
| **Analyst** | — | — | — | — | — | Slot 1 `"4231"` | Slot 2 `0–255` | — | Slots 3–4 | Slot 5 |
| **Scout** | — | — | — | — | — | — | Slot 1 `0–255` | — | Slots 2–5 | — |
| **Commander** | — | — | — | — | — | — | — | Slot 1 `1–6` | Slot 3 | Slots 2, 4–5 |

**Reading this matrix:** To author a command for the Engineer, you can use `SET_SLIDER` (targets Slot 1), `SET_TOGGLE` (targets Slots 3, 4, or 5), or `PRESS_BUTTON` (targets Slot 2). You cannot ask the Engineer to `SCAN_NFC` — they don't have that hardware.

**T2 symmetry:** Each T2 action type (`SET_SLIDER`, `SET_ENCODER`, `SET_ROTARY_SW`, `MATCH_WAVE`) appears on exactly two archetypes — once as a Slot 1 signature control and once as a Slot 2 medium control. This ensures every archetype has T1, T2, and T3 command variety.

### Shared Actions (All Archetypes)

These target **base tablet components** present on every archetype and are not slot-specific:

| Action | Component | Notes |
|---|---|---|
| `CRISIS_BTN` | Crisis Button (guarded illuminated pushbutton) | Crisis events — every player has one |
| `SUBMIT` | Submit Button | Not a command action; used to lock in analog values |

### Command Complexity Tiers

Commands are classified by how much cognitive/physical effort they require. The Hub uses this for pacing — it won't stack three high-complexity commands on the same player back-to-back.

| Tier | Description | Action Types | Avg. Execution Time |
|---|---|---|---|
| **T1 — Quick** | Binary flip or press. Instant. | `SET_TOGGLE`, `PRESS_BUTTON` | 1–2 seconds |
| **T2 — Standard** | Moderate precision or matching. Requires aiming. | `SET_SLIDER`, `SET_ENCODER`, `SET_ROTARY_SW`, `MATCH_WAVE` | 3–6 seconds |
| **T3 — Complex** | Multi-step or high precision. Requires focus. | `SET_JOYSTICK`, `MATCH_COLOR`, `ENTER_CODE`, `SCAN_NFC` | 5–12 seconds |

The Mission Architect tags every command with its tier. The Hub's difficulty system uses this to balance workload.

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
  "command_pools": { },
  "crises": [ ],
  "phases": [ ],
  "outcomes": { },
  "narrator": { }
}
```

### Metadata

```json
"meta": {
  "id": "PIRATE_HUNT_01",
  "title": "The Crimson Galleon",
  "pack": "PIRATE_ADVENTURES",
  "theme": "pirate",
  "subject": "teamwork",
  "age_rating": "8+",
  "difficulty": "medium",
  "player_count": { "min": 2, "max": 8 },
  "duration_sec": { "min": 180, "max": 420 },
  "version": "1.0.0",
  "author": "mission_architect"
}
```

| Field | Description |
|---|---|
| `id` | Unique scenario identifier (matches NFC card payload) |
| `pack` | Parent game pack this scenario belongs to |
| `theme` | Theme key — drives role names and OLED labels |
| `subject` | Optional educational subject (for school/STEM packs) |
| `player_count` | Scenario works with this range of connected archetypes |
| `duration_sec` | Approximate game duration (Hub targets this range) |

### Role Map

Maps generic archetype IDs to theme-specific narrative role names. The Hub pushes these to tablet command screens.

```json
"roles": {
  "NAVIGATOR":  "Quartermaster",
  "ENGINEER":   "Ship's Carpenter",
  "OPERATOR":   "Signalman",
  "SENTINEL":   "Master-at-Arms",
  "MEDIC":      "Surgeon",
  "ANALYST":    "Cartographer",
  "SCOUT":      "Lookout",
  "COMMANDER":  "Bosun"
}
```

A scenario only needs to define roles for the archetypes it supports. If 3 archetypes connect that aren't in the role map, the Hub uses generic fallback names.

### OLED Label Map

Five narrative labels per archetype, sent via `OLED_LABELS` at scenario load.

```json
"oled_labels": {
  "NAVIGATOR": ["Ship's Wheel", "Anchor Release", "Port Sail", "Starboard Sail", "Mark Position"],
  "ENGINEER":  ["Sail Hoist", "Fire Cannons", "Bilge Pump", "Cargo Hatch", "Gunport Doors"],
  "SENTINEL":  ["Captain's Seal", "Brace for Impact", "Armor Plating", "Boarding Nets", "Ring Bell"],
  "MEDIC":     ["Brew Tonic", "Apply Poultice", "Sickbay Lantern", "Check Pulse", "Call for Rum"],
  "ANALYST":   ["Chart Course", "Decode Signal", "Compass Bearing", "Star Chart", "Log Entry"],
  "SCOUT":     ["Spyglass Sweep", "Stealth Mode", "Port Watch", "Starboard Watch", "Crow's Nest"],
  "OPERATOR":  ["Signal Flags", "Emergency Flare", "Semaphore", "Hail Ship", "Send Warning"],
  "COMMANDER": ["Fleet Formation", "Give the Order", "Flag Signals", "Bosun's Whistle", "Ship's Log"]
}
```

Label order matches slot order (index 0 = Slot 1, etc.).

### Command Pools

The core of the scenario. Each pool is a named bucket of commands that the Hub draws from during the frantic phase. Commands are **never hardcoded in sequence** — the Hub randomly selects from pools, ensuring replayability.

```json
"command_pools": {
  "direct": [
    {
      "id": "nav_steer_port",
      "target_arch": "NAVIGATOR",
      "action": "SET_JOYSTICK",
      "slot": 1,
      "tier": "T3",
      "label": "Hard to port!",
      "narrator_line": "Quartermaster! Hard to port — reef ahead!",
      "value": { "x": -80, "y": 0 },
      "tolerance": { "x": 15, "y": 20 },
      "timeout_ms": 8000
    },
    {
      "id": "eng_full_sail",
      "target_arch": "ENGINEER",
      "action": "SET_SLIDER",
      "slot": 1,
      "tier": "T2",
      "label": "Full sail!",
      "narrator_line": "Carpenter! Hoist the mainsail — full speed!",
      "value": 100,
      "tolerance": 10,
      "timeout_ms": 5000
    },
    {
      "id": "sent_scan_red",
      "target_arch": "SENTINEL",
      "action": "SCAN_NFC",
      "slot": 1,
      "tier": "T3",
      "label": "Scan the RED seal!",
      "narrator_line": "Master-at-Arms! I need the crimson captain's seal — NOW!",
      "value": "RED_SEAL",
      "timeout_ms": 10000
    },
    {
      "id": "med_green_tonic",
      "target_arch": "MEDIC",
      "action": "MATCH_COLOR",
      "slot": 1,
      "tier": "T3",
      "label": "Mix GREEN tonic!",
      "narrator_line": "Surgeon! The first mate needs the green tonic — mix it!",
      "value": [0, 200, 50],
      "tolerance": 30,
      "timeout_ms": 8000
    },
    {
      "id": "analyst_code_314",
      "target_arch": "ANALYST",
      "action": "ENTER_CODE",
      "slot": 1,
      "tier": "T3",
      "label": "Enter code 3-1-4!",
      "narrator_line": "Cartographer! The map says 3-1-4 — punch it in!",
      "value": "314",
      "timeout_ms": 7000
    },
    {
      "id": "nav_toggle_port",
      "target_arch": "NAVIGATOR",
      "action": "SET_TOGGLE",
      "slot": 3,
      "tier": "T1",
      "label": "Port sail — ON!",
      "narrator_line": "Raise the port sail!",
      "value": true,
      "timeout_ms": 3000
    }
  ],
  "cooperative": [
    {
      "id": "coop_tell_eng_half",
      "display_on": "NAVIGATOR",
      "target_arch": "ENGINEER",
      "action": "SET_SLIDER",
      "slot": 1,
      "tier": "T2",
      "label": "Tell the Carpenter: half sail!",
      "narrator_line": "Quartermaster! Tell the Carpenter — half sail, now!",
      "value": 50,
      "tolerance": 10,
      "timeout_ms": 10000
    },
    {
      "id": "coop_tell_sent_lock",
      "display_on": "MEDIC",
      "target_arch": "SENTINEL",
      "action": "SET_TOGGLE",
      "slot": 3,
      "tier": "T1",
      "label": "Tell the Master-at-Arms: armor ON!",
      "narrator_line": "Surgeon! Shout to the Master-at-Arms — raise the armor plating!",
      "value": true,
      "timeout_ms": 6000
    }
  ]
}
```

#### Command Object Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes | Unique command identifier within this scenario |
| `target_arch` | `string` | Yes | Archetype that must physically execute the action |
| `action` | `string` | Yes | Protocol action type (must match [capability matrix](#action-types-per-archetype)) |
| `slot` | `uint8` | Yes | Which slot on the target archetype (1–5) |
| `tier` | `string` | Yes | `T1`, `T2`, or `T3` — complexity tier |
| `label` | `string` | Yes | Short text shown on the player's command screen |
| `narrator_line` | `string` | Yes | Full narrator voice line (for audio playback on Hub) |
| `value` | varies | Yes | Target value the player must achieve |
| `tolerance` | varies | No | Acceptable deviation from `value` (for analog controls). Omit for binary actions. |
| `timeout_ms` | `uint16` | Yes | Time allowed before the command expires |
| `display_on` | `string` | Coop only | Archetype whose screen shows this command (the "shouter") |

#### Pool Types

| Pool | Key | Description |
|---|---|---|
| **Direct** | `direct` | Hub → one player's screen. That player executes the command on their own tablet. |
| **Cooperative** | `cooperative` | Hub → Player A's screen (the "shouter"). Player A must verbally communicate the command to Player B (the "executor"). Player B executes it on their tablet. Tests communication under pressure. |

> **Crisis events** are defined separately (see below) because they operate on different mechanics.

### Crisis Events

Crises interrupt normal command flow. They target **all players** (via the Crisis Button) or **subsets** (via specific controls).

```json
"crises": [
  {
    "id": "crisis_hull_breach",
    "type": "CRISIS_ALL",
    "label": "HULL BREACH!",
    "narrator_line": "HULL BREACH! ALL HANDS — BRACE! BRACE! BRACE!",
    "required_count": "all",
    "timeout_ms": 5000,
    "penalty": "health_major"
  },
  {
    "id": "crisis_fire_below",
    "type": "CRISIS_THRESHOLD",
    "label": "FIRE BELOW DECKS!",
    "narrator_line": "Fire in the hold! I need at least three of you — SMASH THAT BUTTON!",
    "required_count": 3,
    "timeout_ms": 6000,
    "penalty": "health_minor"
  },
  {
    "id": "crisis_rogue_wave",
    "type": "MULTI_ACTION",
    "label": "ROGUE WAVE INCOMING!",
    "narrator_line": "ROGUE WAVE! Navigator — hard starboard! Engineer — cut the sails! Everyone else — BRACE!",
    "actions": [
      { "target_arch": "NAVIGATOR", "action": "SET_JOYSTICK", "slot": 1, "value": { "x": 100, "y": 0 }, "tolerance": { "x": 20, "y": 30 } },
      { "target_arch": "ENGINEER", "action": "SET_SLIDER", "slot": 1, "value": 0, "tolerance": 10 },
      { "rest": "CRISIS_BTN" }
    ],
    "timeout_ms": 7000,
    "penalty": "health_major"
  }
]
```

#### Crisis Types

| Type | Mechanic |
|---|---|
| `CRISIS_ALL` | All connected players must press their Crisis Button within the timeout. |
| `CRISIS_THRESHOLD` | At least `required_count` players must press the Crisis Button. |
| `MULTI_ACTION` | Named archetypes execute specific commands; remaining players press the Crisis Button. Most dramatic. |

### Phase Definitions

Phases control pacing, difficulty, and **narrative branching** across the game session. Every standard scenario follows a fixed structure:

```
 INTRO ─► FRANTIC 1 ─► BRANCH 1 ─► FRANTIC 2 ─► BRANCH 2 ─► FRANTIC 3 ─► BRANCH 3 ─► ENDING
```

This creates a **2×2×2 branching tree = 8 distinct narrative paths** per scenario:

```
                                                          ┌─ W ── Path A (WWW)
                                      ┌─ W ── Frantic 3 ─┤
                   ┌─ W ── Frantic 2 ─┤                   └─ L ── Path B (WWL)
                   │                  │                    ┌─ W ── Path C (WLW)
                   │                  └─ L ── Frantic 3 ─┤
 INTRO ► Frantic 1 ┤                                      └─ L ── Path D (WLL)
                   │                                      ┌─ W ── Path E (LWW)
                   │                  ┌─ W ── Frantic 3 ─┤
                   └─ L ── Frantic 2 ─┤                   └─ L ── Path F (LWL)
                                      │                    ┌─ W ── Path G (LLW)
                                      └─ L ── Frantic 3 ─┤
                                                          └─ L ── Path H (LLL)
```

Each branch point evaluates crew performance using the same [performance metrics](#performance-metrics) and composite score. The tier at each checkpoint determines which narrative fork the story takes — different narrator lines, different difficulty tuning for the next phase, and ultimately a different ending.

#### Phase Naming Convention

With 3 branches producing up to 4 variants of Frantic 2 and up to 4 variants of Frantic 3, phases use a path-suffix naming scheme:

| Phase | Variants | IDs |
|---|---|---|
| Frantic 1 | 1 (shared) | `frantic_1` |
| Frantic 2 | 2 (after W or L) | `frantic_2_W`, `frantic_2_L` |
| Frantic 3 | 4 (after WW, WL, LW, LL) | `frantic_3_WW`, `frantic_3_WL`, `frantic_3_LW`, `frantic_3_LL` |

> **Authoring shortcut:** Frantic 2 and 3 variants can share the same command pools — only difficulty tuning and ambient narrator lines need to differ. The story branches through narration and tone, not through entirely different command sets. This keeps authoring effort manageable.

```json
"phases": [
  {
    "id": "intro",
    "type": "NARRATION",
    "duration_sec": 30,
    "narrator_lines": [
      "Welcome aboard The Crimson Galleon, you sorry lot!",
      "We've got wind in our sails and a Royal Navy frigate on our tail.",
      "Stations, everyone. This is going to get rough."
    ]
  },
  {
    "id": "frantic_1",
    "type": "FRANTIC",
    "duration_sec": 90,
    "difficulty": {
      "commands_per_min": { "start": 4, "end": 7 },
      "coop_ratio": 0.2,
      "crisis_chance_per_30s": 0.15,
      "timeout_multiplier": 1.2
    },
    "pools": ["direct", "cooperative"],
    "crises": ["crisis_hull_breach"]
  },
  {
    "id": "branch_1",
    "type": "BRANCH",
    "evaluate": "frantic_1",
    "threshold": 0.55,
    "win": {
      "narrator_lines": [
        "Ha! We're pulling ahead!",
        "The frigate's falling behind — but don't celebrate yet.",
        "They're signaling for reinforcements. Round two, crew!"
      ],
      "next_phase": "frantic_2_W"
    },
    "lose": {
      "narrator_lines": [
        "That was sloppy! The frigate is RIGHT on us!",
        "Half the rigging is torn and the bilge is flooding.",
        "Get it together or we're all going to the brig!"
      ],
      "next_phase": "frantic_2_L"
    }
  },
  {
    "id": "frantic_2_W",
    "type": "FRANTIC",
    "duration_sec": 100,
    "difficulty": {
      "commands_per_min": { "start": 7, "end": 10 },
      "coop_ratio": 0.35,
      "crisis_chance_per_30s": 0.25,
      "timeout_multiplier": 1.0
    },
    "pools": ["direct", "cooperative"],
    "crises": ["crisis_hull_breach", "crisis_fire_below"],
    "narrator_lines_ambient": [
      "Keep the pressure up!",
      "They're trying to flank — stay sharp!"
    ]
  },
  {
    "id": "frantic_2_L",
    "type": "FRANTIC",
    "duration_sec": 100,
    "difficulty": {
      "commands_per_min": { "start": 6, "end": 9 },
      "coop_ratio": 0.40,
      "crisis_chance_per_30s": 0.30,
      "timeout_multiplier": 0.9
    },
    "pools": ["direct", "cooperative"],
    "crises": ["crisis_hull_breach", "crisis_fire_below", "crisis_rogue_wave"],
    "narrator_lines_ambient": [
      "We're taking on water!",
      "The frigate is alongside — MOVE!"
    ]
  },
  {
    "id": "branch_2",
    "type": "BRANCH",
    "evaluate": "current",
    "threshold": 0.55,
    "condition_per_path": {
      "W": {
        "win": {
          "narrator_lines": ["Outstanding! Two for two — they can't touch us!", "One final push and we're free!"],
          "next_phase": "frantic_3_WW"
        },
        "lose": {
          "narrator_lines": ["We had the lead and you BLEW IT!", "One more chance. Don't waste it."],
          "next_phase": "frantic_3_WL"
        }
      },
      "L": {
        "win": {
          "narrator_lines": ["NOW you're awake! That's more like it!", "Redemption is possible — finish strong!"],
          "next_phase": "frantic_3_LW"
        },
        "lose": {
          "narrator_lines": ["This is dire. The ship is falling apart around us.", "Last chance. Everything you've got or we're done."],
          "next_phase": "frantic_3_LL"
        }
      }
    }
  },
  {
    "id": "frantic_3_WW",
    "type": "FRANTIC",
    "duration_sec": 90,
    "difficulty": {
      "commands_per_min": { "start": 10, "end": 14 },
      "coop_ratio": 0.45,
      "crisis_chance_per_30s": 0.35,
      "timeout_multiplier": 0.9
    },
    "pools": ["direct", "cooperative"],
    "crises": ["crisis_hull_breach", "crisis_fire_below", "crisis_rogue_wave"],
    "narrator_lines_ambient": ["Final stretch! Don't let up!", "Almost there!"]
  },
  {
    "id": "frantic_3_WL",
    "type": "FRANTIC",
    "duration_sec": 90,
    "difficulty": {
      "commands_per_min": { "start": 9, "end": 13 },
      "coop_ratio": 0.50,
      "crisis_chance_per_30s": 0.40,
      "timeout_multiplier": 0.85
    },
    "pools": ["direct", "cooperative"],
    "crises": ["crisis_hull_breach", "crisis_fire_below", "crisis_rogue_wave"],
    "narrator_lines_ambient": ["They're closing again!", "Prove that first round wasn't a fluke!"]
  },
  {
    "id": "frantic_3_LW",
    "type": "FRANTIC",
    "duration_sec": 90,
    "difficulty": {
      "commands_per_min": { "start": 9, "end": 13 },
      "coop_ratio": 0.50,
      "crisis_chance_per_30s": 0.35,
      "timeout_multiplier": 0.9
    },
    "pools": ["direct", "cooperative"],
    "crises": ["crisis_hull_breach", "crisis_fire_below", "crisis_rogue_wave"],
    "narrator_lines_ambient": ["Keep this momentum!", "Don't fall back now!"]
  },
  {
    "id": "frantic_3_LL",
    "type": "FRANTIC",
    "duration_sec": 90,
    "difficulty": {
      "commands_per_min": { "start": 8, "end": 12 },
      "coop_ratio": 0.50,
      "crisis_chance_per_30s": 0.45,
      "timeout_multiplier": 0.8
    },
    "pools": ["direct", "cooperative"],
    "crises": ["crisis_hull_breach", "crisis_fire_below", "crisis_rogue_wave"],
    "narrator_lines_ambient": ["We're sinking!", "This is it — do or die!"]
  },
  {
    "id": "branch_3",
    "type": "BRANCH",
    "evaluate": "current",
    "threshold": 0.55
  }
]
```

The final outcome is determined by combining the three branch results into one of **8 ending paths**:

| Branch 1 | Branch 2 | Branch 3 | Path | Narrative Arc | Typical Tier |
|---|---|---|---|---|---|
| W | W | W | **A** | Dominant victory | TRIUMPH |
| W | W | L | **B** | Strong start, stumbled at the finish | SUCCESS |
| W | L | W | **C** | Mid-game crisis, recovered | SUCCESS |
| W | L | L | **D** | Promising start, fell apart | SURVIVE or FAILURE |
| L | W | W | **E** | Rocky start, full redemption | SUCCESS |
| L | W | L | **F** | Inconsistent crew | SURVIVE |
| L | L | W | **G** | Last-second miracle | SURVIVE |
| L | L | L | **H** | Total collapse | FAILURE or DISASTER |

Each path has its own set of ending narrator lines in the `outcomes` section (see [Outcome Endings](#outcome-endings)).

> **Note:** Health reaching 0 at any point during a frantic phase triggers an immediate DISASTER ending, bypassing the normal branch flow — the ship sinks, the station explodes, game over.

#### Phase Types

| Type | Description |
|---|---|
| `NARRATION` | Hub plays narrator lines. No commands issued. Sets the scene. |
| `FRANTIC` | Active gameplay. Hub draws commands from pools at the specified rate. |
| `BRANCH` | Hub pauses, evaluates metrics from the preceding frantic phase, selects a narrative fork, plays branch narrator lines, then jumps to the chosen next phase. |

#### Branch Object Fields

| Field | Type | Description |
|---|---|---|
| `evaluate` | `string` | Which frantic phase's metrics to evaluate. `"frantic_1"` or `"current"` for the most recent. |
| `threshold` | `float` | Composite score threshold for WIN. Score >= threshold = WIN, below = LOSE. |
| `win.narrator_lines` | `string[]` | Narrator lines played if WIN. |
| `win.next_phase` | `string` | Phase ID to jump to after WIN narration. |
| `lose.narrator_lines` | `string[]` | Narrator lines played if LOSE. |
| `lose.next_phase` | `string` | Phase ID to jump to after LOSE narration. |
| `condition_per_path` | `object` | For branches 2+, keyed by prior path string (e.g., `"W"`, `"L"`). Each key contains its own `win`/`lose` with path-specific narrator lines and next phases. |

#### Difficulty Parameters

| Parameter | Description |
|---|---|
| `commands_per_min` | Command issue rate. Ramps from `start` to `end` over the phase duration. |
| `coop_ratio` | Fraction of commands drawn from the `cooperative` pool (0.0–1.0). Higher = more cross-table shouting. |
| `crisis_chance_per_30s` | Probability of a crisis event firing in each 30-second window. |
| `timeout_multiplier` | Multiplied against each command's base `timeout_ms`. < 1.0 tightens windows; > 1.0 loosens. |

#### Authoring Effort: Scaling Content Across 8 Paths

Branching doesn't mean writing 8 completely separate games. Content is layered:

| Content Layer | Shared or Per-Path | Count |
|---|---|---|
| Command pools (direct + cooperative) | **Shared** — all paths draw from the same pools | 1 set |
| Crisis events | **Shared** — same crises, different probabilities per path | 1 set |
| Difficulty tuning per frantic variant | **Per-path** — 1 + 2 + 4 = 7 total frantic phases | 7 |
| Branch narrator lines (transitions) | **Per-branch** — 2 + 4 + 0 = 6 transition narrations | 6 |
| Ending narrator lines | **Per-path** — 8 unique endings + 1 disaster | 9 |
| Ambient narrator lines per frantic variant | **Per-path** — 2–4 lines each | ~20 lines |

**Total unique narration per scenario:** ~9 endings + ~6 transitions + ~20 ambient lines = **~35 narration blocks**. The command/crisis content is fully shared, so the marginal cost of 8 paths vs. 4 is mostly narrator writing.

---

## Outcome & Branching System

This is the heart of replayability beyond command randomization. Scenarios have **multiple endings** determined by how the crew performed across specific dimensions.

### Performance Metrics

The Hub tracks these metrics in real time during the frantic phase. They are the raw inputs to outcome evaluation.

| Metric | Key | How It's Tracked | Description |
|---|---|---|---|
| **Direct Execution Rate** | `direct_rate` | Successful direct commands / total direct commands issued | How well each player executed commands on their own device. |
| **Cooperative Success Rate** | `coop_rate` | Successful coop commands / total coop commands issued | How well the team communicated across tablets. Measures shouting accuracy AND execution by the receiving player. |
| **Timeout Rate** | `timeout_rate` | Expired commands / total commands issued | How many commands the crew simply ran out of time on. |
| **Crisis Response Rate** | `crisis_rate` | Successful crisis responses / total crises | How reliably the crew hit the Crisis Button (or executed crisis actions) in time. |
| **Average Response Time** | `avg_response_ms` | Mean time from command issue to successful execution | Overall speed. Faster = more skilled crew. |
| **Ship Health** | `health` | Starts at 100, decreased by failed commands and crises | The "HP bar." Reaching 0 triggers immediate game-over. |

#### Per-Player Tracking

The Hub also tracks metrics **per player** for post-game scoring:

| Per-Player Metric | Description |
|---|---|
| `commands_received` | Total commands dispatched to this player |
| `commands_succeeded` | Commands executed correctly |
| `commands_failed` | Commands executed incorrectly (wrong value) |
| `commands_expired` | Commands that timed out |
| `avg_response_ms` | This player's average response time |
| `coop_sent` | Cooperative commands this player had to shout |
| `coop_sent_success` | How many of those were successfully executed by the target |
| `crises_responded` | Crisis events this player responded to in time |

### Branch Conditions

At each branch point, the Hub computes the `composite_score` for the frantic phase that just ended and compares it to the branch `threshold`. Score >= threshold = WIN, below = LOSE. This is simple and binary at each checkpoint — the nuanced diagnostic analysis (communication failure vs. execution failure vs. timeout failure) happens at the **final ending**, where the Hub has cumulative data from all three phases.

### Outcome Endings

The `outcomes` section maps each of the 8 paths (plus the disaster bailout) to a unique set of narrator lines and a tier.

```json
"outcomes": {
  "metrics_weights": {
    "direct_rate":  0.30,
    "coop_rate":    0.30,
    "timeout_rate": 0.20,
    "crisis_rate":  0.20
  },
  "disaster": {
    "tier": "DISASTER",
    "narrator_lines": [
      "She's going down! Abandon ship!",
      "The Crimson Galleon slips beneath the waves... along with your reputation."
    ]
  },
  "endings": {
    "WWW": {
      "tier": "TRIUMPH",
      "narrator_lines": [
        "LEGENDARY!",
        "The Crimson Galleon doesn't just escape — you turn and fire a broadside as you pass.",
        "The Royal Navy retreats in shame. Songs will be written about this crew.",
        "Now... who wants to count the treasure?"
      ]
    },
    "WWL": {
      "tier": "SUCCESS",
      "narrator_lines": [
        "So close to perfection!",
        "You had them beat — then stumbled at the finish line.",
        "The Galleon escapes into the fog, but that last round was rough.",
        "A good crew. Almost a great one."
      ]
    },
    "WLW": {
      "tier": "SUCCESS",
      "narrator_lines": [
        "A rocky middle chapter, but you pulled it together!",
        "The frigate had us for a moment there — then you found your rhythm again.",
        "The Crimson Galleon sails free. Well recovered, crew."
      ]
    },
    "WLL": {
      "tier": "SURVIVE",
      "sub_analysis": true,
      "narrator_lines": [
        "Started strong, then fell apart.",
        "The Galleon limps into port with half the crew ready to mutiny.",
        "You escaped... barely. Figure out what went wrong in those last two rounds."
      ]
    },
    "LWW": {
      "tier": "SUCCESS",
      "narrator_lines": [
        "The redemption arc!",
        "A terrible start — but then something clicked.",
        "You clawed your way back and outran the frigate through sheer determination.",
        "That's the kind of crew stories are made of."
      ]
    },
    "LWL": {
      "tier": "SURVIVE",
      "sub_analysis": true,
      "narrator_lines": [
        "Up and down like the waves themselves.",
        "One good round sandwiched between two bad ones doesn't inspire confidence.",
        "The Galleon escapes, but the crew needs consistency."
      ]
    },
    "LLW": {
      "tier": "SURVIVE",
      "narrator_lines": [
        "A last-second miracle!",
        "Two rounds of chaos and then — somehow — you pulled it out of the fire.",
        "Don't count on miracles next time. Start stronger."
      ]
    },
    "LLL": {
      "tier": "FAILURE",
      "sub_analysis": true,
      "narrator_lines": [
        "Three rounds. Three failures.",
        "The frigate catches The Crimson Galleon and boards her without resistance.",
        "The crew is captured. The treasure is gone. The legend ends here."
      ]
    }
  }
}
```

#### Sub-Analysis (Diagnostic Endings)

When `sub_analysis` is `true` on an ending, the Hub appends **diagnostic narrator lines** after the main ending based on which performance dimension was weakest. This tells the crew *why* they struggled:

| Weakest Metric | Diagnostic Lines |
|---|---|
| `coop_rate` (< 0.40) | "The problem? Communication. You each worked your own controls fine, but nobody was relaying orders across the table." |
| `direct_rate` (< 0.45) | "You were talking to each other — that's good. But half of you couldn't execute when it mattered. Know your controls." |
| `timeout_rate` (> 0.40) | "Too slow. Orders expired while you were still fumbling. Speed comes with practice." |
| `crisis_rate` (< 0.50) | "When the crises hit, nobody responded. Those crisis buttons exist for a reason." |

Only SURVIVE and FAILURE endings use sub-analysis. TRIUMPH and SUCCESS don't need diagnosis — they earned it. DISASTER speaks for itself (health hit 0).

### Outcome Tiers

Every ending maps to one of five tiers. The tier determines the ending's tone, the score screen presentation, and any unlock rewards.

| Tier | Description | Score Multiplier |
|---|---|---|
| **DISASTER** | Ship health reached 0. Total failure. Game ended early. | 0.0× |
| **FAILURE** | All three phases lost. Constructive diagnostic feedback. | 0.5× |
| **SURVIVE** | Mixed results. Scraped through but needs improvement. | 1.0× |
| **SUCCESS** | Solid performance across most phases. The crew worked well. | 1.5× |
| **TRIUMPH** | All three phases won. Near-perfect coordination and speed. | 2.0× |

### How the Hub Evaluates Outcomes

The evaluation flow across the whole game:

1. **After each frantic phase:** Hub computes `composite_score` for that phase. Compares to branch `threshold`. Selects WIN or LOSE. Plays branch narrator lines. Advances to the appropriate next frantic phase.
2. **Health check (continuous):** If `health` reaches 0 during any frantic phase, Hub immediately enters DISASTER ending — bypasses all remaining phases and branches.
3. **After Branch 3:** Hub combines the three W/L results into a path key (e.g., `"WLW"`). Looks up the corresponding ending in `outcomes.endings`.
4. **If `sub_analysis` is true:** Hub identifies the weakest cumulative metric across all three phases and appends diagnostic narrator lines.
5. Hub sends `GAME_OVER` with outcome tier, path, and score to all tablets.
6. Hub enters score phase: sends `SCORE_SUMMARY` with per-player stats.

**Fallback:** If a path key doesn't exist in `outcomes.endings` (shouldn't happen), the Hub uses a generic "mission complete" message.

---

## Difficulty & Pacing

### Difficulty Curves

Each frantic phase defines a `commands_per_min` ramp (start → end) over its duration. Combined with the `timeout_multiplier`, this creates the escalating pressure curve. Because the game branches, the difficulty depends on which path the crew is on:

```
Commands/min
     14 │                                  ╱── frantic_3_WW (dominant path)
        │                            ╱────╱
     12 │                      ╱────╱───── frantic_3_WL / frantic_3_LW
        │                ╱────╱
     10 │          ╱────╱
        │    ╱────╱─────────── frantic_3_LL (survival path)
      7 │───╱── frantic_2_W
      6 │──── frantic_2_L
      4 │── frantic_1
        │
        └─────────────────────────────────────→ Time
         0     90    190                  280 sec
```

**Key insight:** The WIN path ramps harder (the crew proved they can handle it). The LOSE path avoids death-spiraling — difficulty stays high but doesn't punish as aggressively, giving the crew a chance to recover.

The scenario also controls **coop_ratio** escalation — early phases favor direct commands (players learn their own controls), later phases increase cooperative commands (forces team communication as pressure mounts). Lose-path variants push coop_ratio higher earlier, because the most common failure mode is poor communication.

### Adaptive Pacing

The Hub can optionally adjust pacing in real time based on crew performance. This is a **Hub firmware feature**, not a scenario field — but scenarios can enable/disable it.

```json
"meta": {
  "adaptive_pacing": true
}
```

When enabled:
- If `timeout_rate` exceeds 50% over a 30-second window → Hub reduces `commands_per_min` by 20% and increases `timeout_multiplier` by 0.2.
- If `timeout_rate` drops below 10% → Hub increases rate by 10% (up to phase max).
- This prevents death spirals (team gets overwhelmed → more timeouts → worse score → less fun) and keeps skilled teams challenged.

Adaptive pacing is recommended for family/casual packs and disabled for competitive/timed packs.

---

## Replayability Mechanisms

A single scenario file supports high replayability through multiple layers:

| Layer | Mechanism | Impact |
|---|---|---|
| **Command randomization** | Hub randomly draws from pools each run. Order is never the same. | Every session has different command sequences. |
| **Archetype composition** | Different player counts and archetype combinations change which commands are available. | A 4-player game feels different from an 8-player game with the same scenario. |
| **Cooperative command routing** | Which player gets told to shout which command is randomized. | Communication patterns shift every run. |
| **Crisis timing** | Crises fire probabilistically, not on fixed timers. | Crises hit at unpredictable moments. |
| **8-path branching** | 3 branch points × WIN/LOSE = 8 narrative paths with unique endings. | Players get different story arcs — motivates replay to explore other paths and "get the TRIUMPH ending." |
| **Adaptive difficulty** | Real-time pacing adjusts to crew skill. | Same scenario scales naturally from beginners to experts. |
| **Per-player scoring** | Individual + team metrics on the score screen. | Players compete to improve personal stats even on repeat plays. |

This means a $10 NFC card with 3–5 scenarios has dozens of meaningfully different play sessions in it.

---

## Mission Architect (Content Engine)

The Mission Architect is the internal tool (structured LLM prompt system) that generates scenario files conforming to this schema.

### Inputs

| Input | Type | Description |
|---|---|---|
| `theme` | String | The narrative world (space, pirate, submarine, fantasy, etc.) |
| `subject` | String | Optional educational subject (math, history, science) |
| `age_rating` | String | Target age group (8+, 12+, 18+) |
| `difficulty` | String | Base difficulty (easy, medium, hard) |
| `pack_name` | String | Parent game pack identifier |
| `scenario_count` | Integer | Number of scenarios to generate for this pack |
| `archetype_focus` | List | Which archetypes to emphasize (or "all") |
| `duration_target` | Integer | Target game duration in seconds |

### Generation Pipeline

```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│  1. Theme &    │    │  2. Command    │    │  3. Phase &    │
│  Role Mapping  │───►│  Pool Build    │───►│  Difficulty    │
│                │    │                │    │  Curve Design  │
└────────────────┘    └────────────────┘    └────────────────┘
                                                    │
┌────────────────┐    ┌────────────────┐            │
│  5. Validation │◄───│  4. Outcome    │◄───────────┘
│  & Output      │    │  Branch Author │
└────────────────┘    └────────────────┘
```

1. **Theme & Role Mapping** — Generate `roles` and `oled_labels` based on theme and archetype list.
2. **Command Pool Build** — Generate `direct` and `cooperative` command pools using the [capability matrix](#action-types-per-archetype). Each archetype gets a balanced mix of T1/T2/T3 commands. Cooperative commands are authored with cross-archetype pairings.
3. **Phase & Difficulty Curve** — Design the phase sequence with ramping command rates, coop ratios, and crisis probabilities.
4. **Outcome Branch Author** — Write branch transition narrator lines (6 transitions) and 8 unique path endings (WWW through LLL) plus the disaster bailout. Add `sub_analysis` diagnostic lines for SURVIVE and FAILURE endings.
5. **Validation & Output** — Run the scenario through validation rules (see below), ensure payload sizes fit, output the final JSON.

### Validation Rules

Every generated scenario must pass:

| Rule | Check |
|---|---|
| **Capability compliance** | Every command's `action` + `target_arch` + `slot` must exist in the [capability matrix](#action-types-per-archetype). No asking the Engineer to `SCAN_NFC`. |
| **Pool coverage** | Every connected archetype must have at least 5 direct commands and 2 cooperative commands in the pools. No archetype sits idle. |
| **Tier balance** | Each archetype's command pool must contain at least 40% T1, at least 20% T2, and at least 15% T3 commands. Prevents all-complex or all-trivial loadouts. |
| **Coop pairing diversity** | Cooperative commands must use at least 3 different "shouter → executor" archetype pairs. No single pair dominates. |
| **Timeout sanity** | T1 commands: 2000–5000ms. T2 commands: 3000–8000ms. T3 commands: 5000–12000ms. No absurd deadlines. |
| **Crisis minimum** | At least 2 distinct crisis events per scenario. |
| **Outcome coverage** | Scenario must define all 8 path endings (WWW through LLL) plus the disaster ending. Each ending must have a tier and at least 2 narrator lines. |
| **Payload budget** | No single `COMMAND` message (including label and value) can exceed ~200 bytes when serialized to JSON (leaving headroom in the 250-byte ESP-NOW limit). |
| **Duration feasibility** | Total phase durations must sum to within the `duration_sec` range defined in metadata. |
| **Label length** | OLED labels max 16 characters. Screen labels max 40 characters. Narrator lines max 200 characters. |
| **Unique IDs** | All command `id`s and crisis `id`s must be unique within the scenario. |

---

## Example Scenario (Abridged)

Below is a minimal but complete scenario demonstrating the 3-phase branching schema. Command pools and crises are shared across all paths — only `phases` and `outcomes` reflect the branching structure. A real scenario would have 50+ commands per pool.

```json
{
  "schema_version": "1.0",
  "meta": {
    "id": "PIRATE_HUNT_01",
    "title": "The Crimson Galleon",
    "pack": "PIRATE_ADVENTURES",
    "theme": "pirate",
    "subject": "teamwork",
    "age_rating": "8+",
    "difficulty": "medium",
    "player_count": { "min": 2, "max": 8 },
    "duration_sec": { "min": 180, "max": 420 },
    "adaptive_pacing": true,
    "version": "1.0.0",
    "author": "mission_architect"
  },
  "roles": {
    "NAVIGATOR":  "Quartermaster",
    "ENGINEER":   "Ship's Carpenter",
    "OPERATOR":   "Signalman",
    "SENTINEL":   "Master-at-Arms",
    "MEDIC":      "Surgeon",
    "ANALYST":    "Cartographer",
    "SCOUT":      "Lookout",
    "COMMANDER":  "Bosun"
  },
  "oled_labels": {
    "NAVIGATOR": ["Ship's Wheel", "Anchor Release", "Port Sail", "Starboard Sail", "Mark Position"],
    "ENGINEER":  ["Sail Hoist", "Fire Cannons", "Bilge Pump", "Cargo Hatch", "Gunport Doors"],
    "OPERATOR":  ["Signal Flags", "Emergency Flare", "Semaphore", "Hail Ship", "Send Warning"],
    "SENTINEL":  ["Captain's Seal", "Brace for Impact", "Armor Plating", "Boarding Nets", "Ring Bell"],
    "MEDIC":     ["Brew Tonic", "Apply Poultice", "Sickbay Lantern", "Check Pulse", "Call for Rum"],
    "ANALYST":   ["Chart Course", "Decode Signal", "Compass Bearing", "Star Chart", "Log Entry"],
    "SCOUT":     ["Spyglass Sweep", "Stealth Mode", "Port Watch", "Starboard Watch", "Crow's Nest"],
    "COMMANDER": ["Fleet Formation", "Give the Order", "Flag Signals", "Bosun's Whistle", "Ship's Log"]
  },
  "command_pools": {
    "direct": [
      { "id": "nav_hard_port",    "target_arch": "NAVIGATOR", "action": "SET_JOYSTICK", "slot": 1, "tier": "T3", "label": "Hard to port!",         "narrator_line": "Quartermaster! Hard to port — reef ahead!",       "value": {"x":-80,"y":0}, "tolerance":{"x":15,"y":20},  "timeout_ms": 8000 },
      { "id": "nav_toggle_port",  "target_arch": "NAVIGATOR", "action": "SET_TOGGLE",   "slot": 3, "tier": "T1", "label": "Port sail — ON!",       "narrator_line": "Raise the port sail!",                           "value": true,                                           "timeout_ms": 3000 },
      { "id": "nav_mark_pos",     "target_arch": "NAVIGATOR", "action": "PRESS_BUTTON", "slot": 5, "tier": "T1", "label": "Mark our position!",    "narrator_line": "Quartermaster! Mark position — NOW!",             "value": null,                                           "timeout_ms": 3000 },
      { "id": "eng_full_sail",    "target_arch": "ENGINEER",  "action": "SET_SLIDER",   "slot": 1, "tier": "T2", "label": "Full sail!",            "narrator_line": "Carpenter! Hoist the mainsail — full speed!",     "value": 100, "tolerance": 10,                           "timeout_ms": 5000 },
      { "id": "eng_fire",         "target_arch": "ENGINEER",  "action": "PRESS_BUTTON", "slot": 2, "tier": "T1", "label": "FIRE CANNONS!",         "narrator_line": "Carpenter — FIRE!",                              "value": null,                                           "timeout_ms": 3000 },
      { "id": "eng_bilge",        "target_arch": "ENGINEER",  "action": "SET_TOGGLE",   "slot": 3, "tier": "T1", "label": "Bilge pump — ON!",      "narrator_line": "Start that bilge pump!",                         "value": true,                                           "timeout_ms": 3000 },
      { "id": "op_tune_47",       "target_arch": "OPERATOR",  "action": "SET_ENCODER",  "slot": 1, "tier": "T2", "label": "Tune to channel 47!",   "narrator_line": "Signalman! Channel 47 — there's a message!",      "value": 47,                                             "timeout_ms": 6000 },
      { "id": "op_flare",         "target_arch": "OPERATOR",  "action": "SET_TOGGLE",   "slot": 2, "tier": "T1", "label": "Emergency flare!",      "narrator_line": "Signalman! Fire the emergency flare!",            "value": true,                                           "timeout_ms": 3000 },
      { "id": "sent_red_seal",    "target_arch": "SENTINEL",  "action": "SCAN_NFC",     "slot": 1, "tier": "T3", "label": "Scan the RED seal!",    "narrator_line": "Master-at-Arms! Crimson seal — NOW!",             "value": "RED_SEAL",                                     "timeout_ms": 10000 },
      { "id": "sent_armor",       "target_arch": "SENTINEL",  "action": "SET_TOGGLE",   "slot": 3, "tier": "T1", "label": "Armor plating — UP!",   "narrator_line": "Raise the armor plating!",                       "value": true,                                           "timeout_ms": 3000 },
      { "id": "med_green_tonic",  "target_arch": "MEDIC",     "action": "MATCH_COLOR",  "slot": 1, "tier": "T3", "label": "Mix GREEN tonic!",      "narrator_line": "Surgeon! Green tonic for the first mate!",        "value": [0,200,50], "tolerance": 30,                    "timeout_ms": 8000 },
      { "id": "med_administer",   "target_arch": "MEDIC",     "action": "SET_TOGGLE",   "slot": 2, "tier": "T1", "label": "Administer!",           "narrator_line": "Surgeon! Give him the medicine!",                 "value": true,                                           "timeout_ms": 3000 },
      { "id": "ana_code_314",     "target_arch": "ANALYST",   "action": "ENTER_CODE",   "slot": 1, "tier": "T3", "label": "Enter code 3-1-4!",     "narrator_line": "Cartographer! The map says 3-1-4!",               "value": "314",                                          "timeout_ms": 7000 },
      { "id": "ana_decode",       "target_arch": "ANALYST",   "action": "PRESS_BUTTON", "slot": 2, "tier": "T1", "label": "Decode the signal!",    "narrator_line": "Cartographer! Decode that signal!",               "value": null,                                           "timeout_ms": 3000 },
      { "id": "sco_sweep_180",    "target_arch": "SCOUT",     "action": "MATCH_WAVE",   "slot": 1, "tier": "T2", "label": "Sweep to 180!",         "narrator_line": "Lookout! Sweep the spyglass to 180!",             "value": 180,                                            "timeout_ms": 6000 },
      { "id": "sco_stealth",      "target_arch": "SCOUT",     "action": "SET_TOGGLE",   "slot": 2, "tier": "T1", "label": "Stealth mode — ON!",    "narrator_line": "Lookout — go dark! Stealth mode!",                "value": true,                                           "timeout_ms": 3000 },
      { "id": "cmd_battle",       "target_arch": "COMMANDER", "action": "SET_ROTARY_SW","slot": 1, "tier": "T2", "label": "BATTLE STATIONS!",      "narrator_line": "Bosun! Set to battle stations — position 4!",     "value": 4,                                              "timeout_ms": 5000 },
      { "id": "cmd_order",        "target_arch": "COMMANDER", "action": "PRESS_BUTTON", "slot": 2, "tier": "T1", "label": "Give the order!",       "narrator_line": "Bosun! Give the order!",                         "value": null,                                           "timeout_ms": 3000 }
    ],
    "cooperative": [
      { "id": "coop_nav_tell_eng",  "display_on": "NAVIGATOR", "target_arch": "ENGINEER",  "action": "SET_SLIDER",   "slot": 1, "tier": "T2", "label": "Tell Carpenter: half sail!",    "narrator_line": "Quartermaster! Tell the Carpenter — half sail!",   "value": 50, "tolerance": 10, "timeout_ms": 10000 },
      { "id": "coop_med_tell_sent", "display_on": "MEDIC",     "target_arch": "SENTINEL",  "action": "SET_TOGGLE",   "slot": 3, "tier": "T1", "label": "Tell Master-at-Arms: armor ON!", "narrator_line": "Surgeon! Shout — raise the armor plating!",       "value": true,                "timeout_ms": 6000 },
      { "id": "coop_eng_tell_nav",  "display_on": "ENGINEER",  "target_arch": "NAVIGATOR", "action": "SET_JOYSTICK", "slot": 1, "tier": "T3", "label": "Tell Quartermaster: hard starboard!", "narrator_line": "Carpenter! Tell the helm — hard starboard!", "value": {"x":80,"y":0}, "tolerance":{"x":15,"y":20}, "timeout_ms": 12000 },
      { "id": "coop_cmd_tell_op",   "display_on": "COMMANDER", "target_arch": "OPERATOR",  "action": "SET_ENCODER",  "slot": 1, "tier": "T2", "label": "Tell Signalman: channel 12!",   "narrator_line": "Bosun! Tell the Signalman — channel 12!",         "value": 12,                  "timeout_ms": 8000 },
      { "id": "coop_sco_tell_ana",  "display_on": "SCOUT",     "target_arch": "ANALYST",   "action": "ENTER_CODE",   "slot": 1, "tier": "T3", "label": "Tell Cartographer: code 2-4-1!", "narrator_line": "Lookout! Shout to the Cartographer — 2-4-1!",     "value": "241",               "timeout_ms": 10000 }
    ]
  },
  "crises": [
    { "id": "crisis_hull_breach", "type": "CRISIS_ALL",       "label": "HULL BREACH!",            "narrator_line": "HULL BREACH! ALL HANDS — BRACE!",                  "required_count": "all",  "timeout_ms": 5000, "penalty": "health_major" },
    { "id": "crisis_fire_below",  "type": "CRISIS_THRESHOLD", "label": "FIRE BELOW DECKS!",       "narrator_line": "Fire in the hold! Three of you — SMASH IT!",        "required_count": 3,      "timeout_ms": 6000, "penalty": "health_minor" },
    { "id": "crisis_rogue_wave",  "type": "MULTI_ACTION",       "label": "ROGUE WAVE!",             "narrator_line": "ROGUE WAVE! Navigator — starboard! Engineer — cut sails! BRACE!", "actions": [{"target_arch":"NAVIGATOR","action":"SET_JOYSTICK","slot":1,"value":{"x":100,"y":0},"tolerance":{"x":20,"y":30}},{"target_arch":"ENGINEER","action":"SET_SLIDER","slot":1,"value":0,"tolerance":10},{"rest":"CRISIS_BTN"}], "timeout_ms": 7000, "penalty": "health_major" }
  ],
  "phases": [
    {
      "id": "intro", "type": "NARRATION", "duration_sec": 30,
      "narrator_lines": ["Welcome aboard The Crimson Galleon, you sorry lot!", "Royal Navy frigate on our tail. Stations, everyone."]
    },
    {
      "id": "frantic_1", "type": "FRANTIC", "duration_sec": 90,
      "difficulty": { "commands_per_min": {"start":4,"end":6}, "coop_ratio": 0.20, "crisis_chance_per_30s": 0.10, "timeout_multiplier": 1.2 },
      "pools": ["direct","cooperative"], "crises": ["crisis_hull_breach"],
      "narrator_lines_ambient": ["Show me what you've got!", "Come on, bilge rats!"]
    },
    {
      "id": "branch_1", "type": "BRANCH", "evaluate": "frantic_1", "threshold": 0.55,
      "win":  { "narrator_lines": ["Not bad! The Galleon pulls ahead!",                  "Keep this pace — we might actually make it."],    "next_phase": "frantic_2_W" },
      "lose": { "narrator_lines": ["Pathetic! The frigate is GAINING!",                  "Get it together or we're done for!"],              "next_phase": "frantic_2_L" }
    },
    {
      "id": "frantic_2_W", "type": "FRANTIC", "duration_sec": 100,
      "difficulty": { "commands_per_min": {"start":7,"end":10}, "coop_ratio": 0.35, "crisis_chance_per_30s": 0.25, "timeout_multiplier": 1.0 },
      "pools": ["direct","cooperative"], "crises": ["crisis_hull_breach","crisis_fire_below"],
      "narrator_lines_ambient": ["Keep the pressure up!", "They're trying to flank — stay sharp!"]
    },
    {
      "id": "frantic_2_L", "type": "FRANTIC", "duration_sec": 100,
      "difficulty": { "commands_per_min": {"start":6,"end":9}, "coop_ratio": 0.40, "crisis_chance_per_30s": 0.30, "timeout_multiplier": 0.9 },
      "pools": ["direct","cooperative"], "crises": ["crisis_hull_breach","crisis_fire_below","crisis_rogue_wave"],
      "narrator_lines_ambient": ["We're taking on water!", "The frigate is alongside — MOVE!"]
    },
    {
      "id": "branch_2", "type": "BRANCH", "evaluate": "current", "threshold": 0.55,
      "condition_per_path": {
        "W": {
          "win":  { "narrator_lines": ["Outstanding! Two for two!",       "One final push and we're free!"],                    "next_phase": "frantic_3_WW" },
          "lose": { "narrator_lines": ["We had the lead and you BLEW IT!", "One more chance. Don't waste it."],                 "next_phase": "frantic_3_WL" }
        },
        "L": {
          "win":  { "narrator_lines": ["NOW you're awake!",               "Redemption is possible — finish strong!"],           "next_phase": "frantic_3_LW" },
          "lose": { "narrator_lines": ["This is dire.",                    "Last chance. Everything you've got or we're done."], "next_phase": "frantic_3_LL" }
        }
      }
    },
    {
      "id": "frantic_3_WW", "type": "FRANTIC", "duration_sec": 90,
      "difficulty": { "commands_per_min": {"start":10,"end":14}, "coop_ratio": 0.45, "crisis_chance_per_30s": 0.35, "timeout_multiplier": 0.9 },
      "pools": ["direct","cooperative"], "crises": ["crisis_hull_breach","crisis_fire_below","crisis_rogue_wave"],
      "narrator_lines_ambient": ["Final stretch! Don't let up!", "Almost there!"]
    },
    {
      "id": "frantic_3_WL", "type": "FRANTIC", "duration_sec": 90,
      "difficulty": { "commands_per_min": {"start":9,"end":13}, "coop_ratio": 0.50, "crisis_chance_per_30s": 0.40, "timeout_multiplier": 0.85 },
      "pools": ["direct","cooperative"], "crises": ["crisis_hull_breach","crisis_fire_below","crisis_rogue_wave"],
      "narrator_lines_ambient": ["They're closing again!", "Prove that first round wasn't a fluke!"]
    },
    {
      "id": "frantic_3_LW", "type": "FRANTIC", "duration_sec": 90,
      "difficulty": { "commands_per_min": {"start":9,"end":13}, "coop_ratio": 0.50, "crisis_chance_per_30s": 0.35, "timeout_multiplier": 0.9 },
      "pools": ["direct","cooperative"], "crises": ["crisis_hull_breach","crisis_fire_below","crisis_rogue_wave"],
      "narrator_lines_ambient": ["Keep this momentum!", "Don't fall back now!"]
    },
    {
      "id": "frantic_3_LL", "type": "FRANTIC", "duration_sec": 90,
      "difficulty": { "commands_per_min": {"start":8,"end":12}, "coop_ratio": 0.50, "crisis_chance_per_30s": 0.45, "timeout_multiplier": 0.8 },
      "pools": ["direct","cooperative"], "crises": ["crisis_hull_breach","crisis_fire_below","crisis_rogue_wave"],
      "narrator_lines_ambient": ["We're sinking!", "This is it — do or die!"]
    },
    {
      "id": "branch_3", "type": "BRANCH", "evaluate": "current", "threshold": 0.55
    }
  ],
  "outcomes": {
    "metrics_weights": { "direct_rate": 0.30, "coop_rate": 0.30, "timeout_rate": 0.20, "crisis_rate": 0.20 },
    "disaster": {
      "tier": "DISASTER",
      "narrator_lines": ["She's going down! Abandon ship!", "The Crimson Galleon slips beneath the waves... along with your reputation."]
    },
    "endings": {
      "WWW": { "tier": "TRIUMPH",  "narrator_lines": ["LEGENDARY!", "You fire a broadside as you pass. Songs will be written about this crew.", "Now... who wants to count the treasure?"] },
      "WWL": { "tier": "SUCCESS",  "narrator_lines": ["So close to perfection!", "The Galleon escapes into the fog, but that last round was rough.", "A good crew. Almost a great one."] },
      "WLW": { "tier": "SUCCESS",  "narrator_lines": ["A rocky middle chapter, but you pulled it together!", "The Crimson Galleon sails free. Well recovered, crew."] },
      "WLL": { "tier": "SURVIVE",  "sub_analysis": true, "narrator_lines": ["Started strong, then fell apart.", "The Galleon limps into port with half the crew ready to mutiny."] },
      "LWW": { "tier": "SUCCESS",  "narrator_lines": ["The redemption arc!", "You clawed your way back. That's the kind of crew stories are made of."] },
      "LWL": { "tier": "SURVIVE",  "sub_analysis": true, "narrator_lines": ["Up and down like the waves themselves.", "The Galleon escapes, but the crew needs consistency."] },
      "LLW": { "tier": "SURVIVE",  "narrator_lines": ["A last-second miracle!", "Don't count on miracles next time. Start stronger."] },
      "LLL": { "tier": "FAILURE",  "sub_analysis": true, "narrator_lines": ["Three rounds. Three failures.", "The crew is captured. The treasure is gone. The legend ends here."] }
    }
  },
  "narrator": {
    "voice": "pirate_captain",
    "tts_engine": "local",
    "between_commands_lines": [
      "Keep it moving!",
      "Faster, you dogs!",
      "The sea waits for no one!",
      "Eyes on your stations!"
    ]
  }
}
```

---

## Appendix: Scenario Size Budget

Scenario data is split across two storage devices on the Hub:

- **Scenario JSON** → ESP32-S3 internal flash (16MB total, ~12MB available after firmware + OTA)
- **Narrator audio** → W25N01GV external SPI NAND flash (128MB, dedicated to audio)

### Scenario JSON (Internal Flash)

| Component | Approx. Size |
|---|---|
| Metadata + roles + labels | ~1 KB |
| Command pools (50 direct + 20 coop) | ~8–12 KB |
| Crises (3–5 events) | ~1 KB |
| Phases (7 frantic + 3 branch + intro = 11 phases) | ~5 KB |
| Outcomes (8 endings + disaster + sub-analysis) | ~4 KB |
| Narrator line text (transitions + ambient + endings) | ~3 KB |
| **Total JSON per scenario** | **~22–28 KB** |
| **Per pack (3–5 scenarios)** | **~80–140 KB** |
| **Internal flash capacity** | **~12 MB → 85–150 packs** |

### Narrator Audio (External SPI NAND)

~60 unique voice lines per scenario (see [Authoring Effort](#authoring-effort-scaling-content-across-8-paths)), ~3 seconds average per line.

| Codec | Per Line | Per Scenario (60 lines) | Per Pack (5 scenarios) | Packs in 128MB |
|---|---|---|---|---|
| Opus 24kbps | ~9 KB | ~540 KB | ~2.7 MB | **~47** |
| MP3 64kbps | ~24 KB | ~1.4 MB | ~7 MB | **~18** |
| ADPCM 16kHz | ~24 KB | ~1.4 MB | ~7 MB | **~18** |

Using Opus (recommended — best quality/size ratio, ESP32-S3 decodes it comfortably), the Hub permanently caches **~47 packs** of narrator audio — more than most customers will ever own.

### Combined Capacity

The bottleneck is audio, not JSON. With Opus encoding:

| | JSON (internal) | Audio (SPI NAND) | Limiting Factor |
|---|---|---|---|
| Per pack | ~100 KB | ~2.7 MB | Audio |
| Total capacity | ~85–150 packs | **~47 packs** | **Audio** |
| Practical limit | — | **~47 packs** | More than enough |

All content is **permanently cached** — downloaded once (over WiFi on first NFC tap or via companion app), never evicted. When flash is full, the companion app shows "Storage full — remove a pack to make room" (like Kindle). At 47 packs × 3–5 scenarios each, that's 140–235 scenarios before storage becomes a concern.
