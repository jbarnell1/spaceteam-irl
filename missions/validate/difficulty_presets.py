"""Difficulty presets for Spaceteam IRL scenarios.

Scenarios reference a difficulty level (easy/medium/hard/extreme) in
meta.difficulty and the runtime resolves per-phase parameters automatically.
Scenarios may still override individual phase difficulty blocks if needed.

This is the modularity layer: scenario JSONs stay lean (just commands,
crises, and narrative) while difficulty tuning lives here as shared presets.
Adjusting a preset instantly re-tunes every scenario that uses it.
"""

from .capability_matrix import FRANTIC_PHASE_IDS

# ─── Difficulty Presets ──────────────────────────────────────────────
# Keys are frantic phase IDs; values are the difficulty dicts the Hub uses.
# "duration_sec" is the base phase length (before adaptive pacing adjusts).

PRESETS = {

    # ── EASY ─────────────────────────────────────────────────────────
    # Gentle ramp. Forgiving timeouts. Low coop and crisis frequency.
    # Great for first-timers, young players, or learning sessions.
    "easy": {
        "frantic_1":    {"commands_per_min": {"start": 2, "end": 3},  "coop_ratio": 0.10, "crisis_chance_per_30s": 0.05, "timeout_multiplier": 1.50, "duration_sec": 260},
        "frantic_2_W":  {"commands_per_min": {"start": 3, "end": 5},  "coop_ratio": 0.20, "crisis_chance_per_30s": 0.10, "timeout_multiplier": 1.30, "duration_sec": 280},
        "frantic_2_L":  {"commands_per_min": {"start": 3, "end": 5},  "coop_ratio": 0.25, "crisis_chance_per_30s": 0.15, "timeout_multiplier": 1.20, "duration_sec": 270},
        "frantic_3_WW": {"commands_per_min": {"start": 5, "end": 7},  "coop_ratio": 0.25, "crisis_chance_per_30s": 0.15, "timeout_multiplier": 1.20, "duration_sec": 280},
        "frantic_3_WL": {"commands_per_min": {"start": 5, "end": 7},  "coop_ratio": 0.30, "crisis_chance_per_30s": 0.20, "timeout_multiplier": 1.10, "duration_sec": 270},
        "frantic_3_LW": {"commands_per_min": {"start": 5, "end": 7},  "coop_ratio": 0.30, "crisis_chance_per_30s": 0.20, "timeout_multiplier": 1.10, "duration_sec": 270},
        "frantic_3_LL": {"commands_per_min": {"start": 4, "end": 6},  "coop_ratio": 0.35, "crisis_chance_per_30s": 0.25, "timeout_multiplier": 1.00, "duration_sec": 260},
    },

    # ── MEDIUM ───────────────────────────────────────────────────────
    # Balanced curve. The baseline Spaceteam experience.
    "medium": {
        "frantic_1":    {"commands_per_min": {"start": 3,  "end": 5},  "coop_ratio": 0.15, "crisis_chance_per_30s": 0.10, "timeout_multiplier": 1.30, "duration_sec": 240},
        "frantic_2_W":  {"commands_per_min": {"start": 5,  "end": 8},  "coop_ratio": 0.30, "crisis_chance_per_30s": 0.20, "timeout_multiplier": 1.10, "duration_sec": 270},
        "frantic_2_L":  {"commands_per_min": {"start": 5,  "end": 7},  "coop_ratio": 0.35, "crisis_chance_per_30s": 0.25, "timeout_multiplier": 1.00, "duration_sec": 250},
        "frantic_3_WW": {"commands_per_min": {"start": 8,  "end": 12}, "coop_ratio": 0.40, "crisis_chance_per_30s": 0.30, "timeout_multiplier": 0.95, "duration_sec": 270},
        "frantic_3_WL": {"commands_per_min": {"start": 7,  "end": 11}, "coop_ratio": 0.45, "crisis_chance_per_30s": 0.35, "timeout_multiplier": 0.90, "duration_sec": 250},
        "frantic_3_LW": {"commands_per_min": {"start": 7,  "end": 11}, "coop_ratio": 0.45, "crisis_chance_per_30s": 0.30, "timeout_multiplier": 0.95, "duration_sec": 250},
        "frantic_3_LL": {"commands_per_min": {"start": 6,  "end": 10}, "coop_ratio": 0.50, "crisis_chance_per_30s": 0.40, "timeout_multiplier": 0.85, "duration_sec": 240},
    },

    # ── HARD ─────────────────────────────────────────────────────────
    # Fast pace, tight timeouts. Demands real coordination.
    "hard": {
        "frantic_1":    {"commands_per_min": {"start": 4,  "end": 7},  "coop_ratio": 0.20, "crisis_chance_per_30s": 0.15, "timeout_multiplier": 1.10, "duration_sec": 220},
        "frantic_2_W":  {"commands_per_min": {"start": 7,  "end": 10}, "coop_ratio": 0.35, "crisis_chance_per_30s": 0.30, "timeout_multiplier": 0.95, "duration_sec": 250},
        "frantic_2_L":  {"commands_per_min": {"start": 6,  "end": 9},  "coop_ratio": 0.40, "crisis_chance_per_30s": 0.35, "timeout_multiplier": 0.90, "duration_sec": 240},
        "frantic_3_WW": {"commands_per_min": {"start": 10, "end": 14}, "coop_ratio": 0.45, "crisis_chance_per_30s": 0.40, "timeout_multiplier": 0.85, "duration_sec": 250},
        "frantic_3_WL": {"commands_per_min": {"start": 9,  "end": 13}, "coop_ratio": 0.50, "crisis_chance_per_30s": 0.45, "timeout_multiplier": 0.80, "duration_sec": 240},
        "frantic_3_LW": {"commands_per_min": {"start": 9,  "end": 13}, "coop_ratio": 0.50, "crisis_chance_per_30s": 0.40, "timeout_multiplier": 0.85, "duration_sec": 240},
        "frantic_3_LL": {"commands_per_min": {"start": 8,  "end": 12}, "coop_ratio": 0.55, "crisis_chance_per_30s": 0.50, "timeout_multiplier": 0.75, "duration_sec": 220},
    },

    # ── EXTREME ──────────────────────────────────────────────────────
    # Relentless. For experienced crews who want near-impossible runs.
    "extreme": {
        "frantic_1":    {"commands_per_min": {"start": 5,  "end": 9},  "coop_ratio": 0.25, "crisis_chance_per_30s": 0.20, "timeout_multiplier": 1.00, "duration_sec": 200},
        "frantic_2_W":  {"commands_per_min": {"start": 9,  "end": 13}, "coop_ratio": 0.40, "crisis_chance_per_30s": 0.40, "timeout_multiplier": 0.85, "duration_sec": 240},
        "frantic_2_L":  {"commands_per_min": {"start": 8,  "end": 12}, "coop_ratio": 0.45, "crisis_chance_per_30s": 0.45, "timeout_multiplier": 0.80, "duration_sec": 230},
        "frantic_3_WW": {"commands_per_min": {"start": 12, "end": 16}, "coop_ratio": 0.50, "crisis_chance_per_30s": 0.50, "timeout_multiplier": 0.75, "duration_sec": 240},
        "frantic_3_WL": {"commands_per_min": {"start": 11, "end": 15}, "coop_ratio": 0.55, "crisis_chance_per_30s": 0.55, "timeout_multiplier": 0.70, "duration_sec": 230},
        "frantic_3_LW": {"commands_per_min": {"start": 11, "end": 15}, "coop_ratio": 0.55, "crisis_chance_per_30s": 0.50, "timeout_multiplier": 0.75, "duration_sec": 230},
        "frantic_3_LL": {"commands_per_min": {"start": 10, "end": 14}, "coop_ratio": 0.60, "crisis_chance_per_30s": 0.60, "timeout_multiplier": 0.65, "duration_sec": 210},
    },
}

DIFFICULTY_LEVELS = list(PRESETS.keys())

# Branch evaluation threshold defaults per difficulty.
# Higher = harder to "win" a branch point.
BRANCH_THRESHOLDS = {
    "easy":    0.45,
    "medium":  0.55,
    "hard":    0.60,
    "extreme": 0.65,
}

# Intro narration duration defaults per difficulty.
INTRO_DURATION = {
    "easy":    75,
    "medium":  60,
    "hard":    50,
    "extreme": 45,
}


def get_preset(difficulty):
    """Return the full preset dict for a difficulty level, or None."""
    return PRESETS.get(difficulty)


def get_phase_params(difficulty, phase_id):
    """Return resolved difficulty parameters for a specific phase, or None."""
    preset = PRESETS.get(difficulty)
    if preset is None:
        return None
    return preset.get(phase_id)


def resolve_phase_difficulty(scenario, phase):
    """Resolve the effective difficulty for a frantic phase.

    Returns the phase's explicit difficulty block if present,
    otherwise falls back to the scenario-level preset.
    """
    if "difficulty" in phase and isinstance(phase["difficulty"], dict):
        return phase["difficulty"]
    difficulty = scenario.get("meta", {}).get("difficulty", "medium")
    return get_phase_params(difficulty, phase["id"])


def estimate_total_commands(difficulty, phase_id):
    """Estimate total commands issued during a frantic phase at a given difficulty."""
    params = get_phase_params(difficulty, phase_id)
    if params is None:
        return 0
    dur = params.get("duration_sec", 0)
    cpm = params.get("commands_per_min", {})
    avg_cpm = (cpm.get("start", 0) + cpm.get("end", 0)) / 2
    return int(avg_cpm * dur / 60)
