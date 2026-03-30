# Author Pipeline

The **author pipeline** decouples creative scenario content from hardware specifics.
Authors write scenarios in a lean **source format** (`.src.json`) using semantic
capability references and named value presets. The **compiler** resolves these into
the materialized runtime JSON the Hub firmware expects.

If hardware changes (e.g., swapping a joystick for a trackball), only the
capability matrix and value presets need updating — not every scenario file.

## Architecture

```
┌─────────────────┐      compile       ┌─────────────────────┐
│  .src.json       │  ───────────────>  │  materialized .json  │
│  (source format) │                    │  (Hub firmware input) │
└─────────────────┘  <───────────────  └─────────────────────┘
                       decompile
```

**Single source of truth chain:**
- `missions/validate/capability_matrix.py` — which archetype has which controls
- `missions/author_pipeline/presets.py` — value presets, tolerances, timeouts
- `missions/scenarios-src/*.src.json` — scenario creative content
- `missions/scenarios/*.json` — compiled output (generated, do not hand-edit)

## Quick Start

All commands use [uv](https://docs.astral.sh/uv/) — no venvs or pip install needed.

```bash
# Compile a source scenario to materialized format
uv run python -m missions.author_pipeline compile missions/scenarios-src/station_omega.src.json -o missions/scenarios/station_omega.json

# Decompile an existing materialized scenario to source format
uv run python -m missions.author_pipeline decompile missions/scenarios/station_omega.json -o missions/scenarios-src/station_omega.src.json

# Validate round-trip integrity on all materialized scenarios
uv run python -m missions.author_pipeline roundtrip missions/scenarios/*.json
```

## Source Format

The source format is identical to the materialized format **except** in command
pools, crises, and preflight, where hardware-specific fields are replaced with
semantic references.

### Direct & Cooperative Commands

**Materialized** (what the Hub sees):
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

**Source** (what authors write):
```json
{
  "id": "nav_hard_port",
  "target_arch": "NAVIGATOR",
  "capability": "specialty_a",
  "label": "Hard to port — debris field!",
  "narrator_line": "Helm! Hard to port — debris field dead ahead!",
  "value_preset": "WEST"
}
```

The compiler derives from the capability matrix and presets:
| Source field | Derived field | How |
|---|---|---|
| `capability` | `action`, `slot` | Looked up in `CAPABILITY_MATRIX[target_arch][capability]` |
| `value_preset` | `value`, `tolerance` | Looked up in `VALUE_PRESETS[action][preset_name]` |
| *(omitted)* | `tier` | Derived from action type via `TIER_ACTIONS` |
| *(omitted)* | `timeout_ms` | Default per action type from `TIMEOUT_DEFAULTS` |

**Cooperative commands** also include `display_on` (which player sees the command on their screen). Coop timeouts use `COOP_TIMEOUT_DEFAULTS` (longer, to account for verbal relay).

### Open Commands

Open commands target `"ANY"` player with the right hardware, so they specify
`action` directly (no archetype to look up):

```json
{
  "id": "open_joystick_evade",
  "target": "ANY",
  "action": "SET_JOYSTICK",
  "label": "Someone — hard evasive LEFT!",
  "narrator_line": "Anyone with a flight stick — hard evasive left!",
  "value_preset": "WEST"
}
```

### Crises

Crisis `actions` entries use `capability` instead of `action` + `slot`:

```json
{
  "target_arch": "ENGINEER",
  "capability": "specialty_a",
  "value_preset": "OFF"
}
```

Non-preset crisis values (e.g., extreme joystick deflections) use raw `value` + `tolerance`:

```json
{
  "target_arch": "NAVIGATOR",
  "capability": "specialty_a",
  "value": {"x": 0, "y": 100},
  "tolerance": {"x": 25, "y": 20}
}
```

The `{"rest": "CRISIS_BTN"}` entries pass through unchanged.

### Preflight

Preflight `init_commands` use `capability` + `value_preset`:

```json
{
  "NAVIGATOR": [
    {"capability": "toggle_1", "value_preset": "OFF"},
    {"capability": "toggle_2", "value_preset": "OFF"},
    {"capability": "specialty_b", "value_preset": "OFF"}
  ]
}
```

### Override Rules

Authors can always override derived values by including them explicitly:

| Override | When to use |
|---|---|
| `"tier": "T2"` | Force a non-standard tier |
| `"tolerance": 15` | Override the preset's tolerance |
| `"timeout_ms": 7000` | Override the default timeout (e.g., shorter codes) |
| `"value": {...}` | Use a raw value instead of a preset |

## Value Presets Reference

### SET_JOYSTICK
| Preset | Value | Tolerance |
|---|---|---|
| `NORTH` | `{"x": 0, "y": 80}` | `{"x": 20, "y": 15}` |
| `SOUTH` | `{"x": 0, "y": -70}` | `{"x": 20, "y": 15}` |
| `EAST` | `{"x": 80, "y": 0}` | `{"x": 15, "y": 20}` |
| `WEST` | `{"x": -80, "y": 0}` | `{"x": 15, "y": 20}` |

### SET_SLIDER
| Preset | Value | Tolerance |
|---|---|---|
| `MAX` | `100` | `10` |
| `HIGH` | `70` | `10` |
| `HALF` | `50` | `10` |
| `LOW` | `20` | `10` |
| `OFF` | `0` | `10` |

### SET_TRIGGER
| Preset | Value | Tolerance |
|---|---|---|
| `FULL` | `100` | `10` |
| `FIRM` | `70` | `10` |
| `HALF` | `50` | `10` |
| `LIGHT` | `30` | `10` |
| `RELEASE` | `0` | `10` |

### SET_TOGGLE
| Preset | Value |
|---|---|
| `ON` | `true` |
| `OFF` | `false` |

### PRESS_BUTTON
| Preset | Value |
|---|---|
| `PRESS` | `null` |

### SET_ROTARY_SW
| Preset | Value |
|---|---|
| `POS_1` – `POS_6` | `1` – `6` |

### MATCH_COLOR
| Preset | Value (RGB) | Tolerance |
|---|---|---|
| `RED` | `[200, 30, 30]` | `30` |
| `GREEN` | `[30, 200, 50]` | `30` |
| `BLUE` | `[0, 80, 200]` | `30` |
| `DEEP_BLUE` | `[30, 60, 200]` | `30` |
| `YELLOW` | `[200, 200, 30]` | `30` |

### PLUG_JACK
| Preset | Value (A→B→C) |
|---|---|
| `NORMAL` | `A→1, B→2, C→3` |
| `BACKUP` | `A→2, B→3, C→1` |
| `BYPASS` | `A→3, B→1, C→2` |
| `EVAC` | `A→1, B→3, C→2` |
| `LOCKDOWN` | `A→2, B→1, C→3` |
| `COMBAT` | `A→3, B→2, C→1` |

### SET_ENCODER / ENTER_CODE / SCAN_NFC
No standard presets — these use scenario-specific raw `value` fields.

## Timeout Defaults (ms)

| Action | Direct / Open | Cooperative |
|---|---|---|
| `SET_TOGGLE` | 3000 | 5000 |
| `PRESS_BUTTON` | 3000 | 5000 |
| `SET_SLIDER` | 5000 | 8000 |
| `SET_ENCODER` | 6000 | 8000 |
| `SET_ROTARY_SW` | 5000 | 8000 |
| `SET_TRIGGER` | 5000 | 8000 |
| `SET_JOYSTICK` | 8000 | 12000 |
| `MATCH_COLOR` | 8000 | 12000 |
| `ENTER_CODE` | 8000 | 12000 |
| `SCAN_NFC` | 10000 | 12000 |
| `PLUG_JACK` | 6000 | 8000 |

## File Layout

```
missions/
├── author_pipeline/
│   ├── __init__.py
│   ├── __main__.py       # CLI (compile / decompile / roundtrip)
│   ├── compiler.py       # Source → materialized
│   ├── decompiler.py     # Materialized → source
│   └── presets.py        # Value presets, tolerance & timeout defaults
├── scenarios-src/        # Source format (what authors edit)
│   ├── station_omega.src.json
│   └── ...
├── scenarios/            # Materialized format (generated, Hub input)
│   ├── station_omega.json
│   └── ...
└── validate/             # Runtime validator (unchanged)
```

## Workflow

1. **Author** edits `.src.json` files in `missions/scenarios-src/`
2. **Compile** to produce materialized JSON: `uv run python -m missions.author_pipeline compile <src> -o <out>`
3. **Validate** the compiled output: `uv run python -m missions.validate <out>`
4. **Round-trip check** after changing presets or capability matrix: `uv run python -m missions.author_pipeline roundtrip missions/scenarios/*.json`

## Adding Value Presets

Edit `missions/author_pipeline/presets.py` and add entries to `VALUE_PRESETS[action_type]`.
Then re-run `roundtrip` to ensure existing scenarios still compile correctly.

## Hardware Changes

If a physical element changes (e.g., joystick replaced with trackball):

1. Update `missions/validate/capability_matrix.py` — change the action type for affected slots
2. Update `missions/author_pipeline/presets.py` — add/modify value presets for the new action type
3. Recompile all source scenarios: the compiler will resolve the new action type automatically
4. Validate: `uv run python -m missions.validate missions/scenarios/*.json`

No scenario source files need to change unless the new hardware has fundamentally
different value semantics (e.g., 2-axis → 1-axis).
