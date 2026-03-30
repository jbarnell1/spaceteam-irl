"""Value presets and defaults for the Spaceteam IRL author pipeline.

Presets decouple scenario content from hardware specifics.  Authors reference
named values (e.g. "WEST" for a joystick deflection) and the compiler resolves
them to the exact JSON the Hub firmware expects.

This file is the ONLY place hardware-specific value formats live.
Changing physical controls?  Update these tables and recompile — no scenario
source files need to change.
"""

# ──────────────────────────────────────────────────────────────────────
# VALUE_PRESETS
# ──────────────────────────────────────────────────────────────────────
# Per-action-type named values.  Each entry maps to the materialized
# "value" (and optionally "tolerance") the Hub expects.

VALUE_PRESETS = {
    "SET_JOYSTICK": {
        "NORTH": {"value": {"x": 0,   "y": 80},  "tolerance": {"x": 20, "y": 15}},
        "SOUTH": {"value": {"x": 0,   "y": -70}, "tolerance": {"x": 20, "y": 15}},
        "EAST":  {"value": {"x": 80,  "y": 0},   "tolerance": {"x": 15, "y": 20}},
        "WEST":  {"value": {"x": -80, "y": 0},   "tolerance": {"x": 15, "y": 20}},
    },
    "SET_SLIDER": {
        "MAX":  {"value": 100, "tolerance": 10},
        "HIGH": {"value": 70,  "tolerance": 10},
        "HALF": {"value": 50,  "tolerance": 10},
        "LOW":  {"value": 20,  "tolerance": 10},
        "OFF":  {"value": 0,   "tolerance": 10},
    },
    "SET_TOGGLE": {
        "ON":  {"value": True},
        "OFF": {"value": False},
    },
    "PRESS_BUTTON": {
        "PRESS": {"value": None},
    },
    "SET_ENCODER": {
        # Encoder values are scenario-specific (freeform integers).
        # Authors typically use raw "value" instead of presets.
    },
    "SET_ROTARY_SW": {
        "POS_1": {"value": 1},
        "POS_2": {"value": 2},
        "POS_3": {"value": 3},
        "POS_4": {"value": 4},
        "POS_5": {"value": 5},
        "POS_6": {"value": 6},
    },
    "MATCH_COLOR": {
        "RED":       {"value": [200, 30, 30],  "tolerance": 30},
        "GREEN":     {"value": [30, 200, 50],  "tolerance": 30},
        "BLUE":      {"value": [0, 80, 200],   "tolerance": 30},
        "DEEP_BLUE": {"value": [30, 60, 200],  "tolerance": 30},
        "YELLOW":    {"value": [200, 200, 30], "tolerance": 30},
    },
    "PLUG_JACK": {
        "NORMAL":   {"value": {"A": "1", "B": "2", "C": "3"}},
        "BACKUP":   {"value": {"A": "2", "B": "3", "C": "1"}},
        "BYPASS":   {"value": {"A": "3", "B": "1", "C": "2"}},
        "EVAC":     {"value": {"A": "1", "B": "3", "C": "2"}},
        "LOCKDOWN": {"value": {"A": "2", "B": "1", "C": "3"}},
        "COMBAT":   {"value": {"A": "3", "B": "2", "C": "1"}},
    },
    "ENTER_CODE": {
        # Code values are scenario-specific strings.
    },
    "SCAN_NFC": {
        # NFC tag IDs are scenario-specific strings.
    },
    "SET_TRIGGER": {
        "FULL":    {"value": 100, "tolerance": 10},
        "FIRM":    {"value": 70,  "tolerance": 10},
        "HALF":    {"value": 50,  "tolerance": 10},
        "LIGHT":   {"value": 30,  "tolerance": 10},
        "RELEASE": {"value": 0,   "tolerance": 10},
    },
}

# ──────────────────────────────────────────────────────────────────────
# TOLERANCE_DEFAULTS
# ──────────────────────────────────────────────────────────────────────
# Fallback tolerance for actions that use it, when not supplied by a
# preset or explicit author override.
TOLERANCE_DEFAULTS = {
    "SET_JOYSTICK": {"x": 15, "y": 20},
    "SET_SLIDER":   10,
    "SET_TRIGGER":  10,
    "MATCH_COLOR":  30,
}

# ──────────────────────────────────────────────────────────────────────
# TIMEOUT_DEFAULTS  (milliseconds)
# ──────────────────────────────────────────────────────────────────────
# Per-action-type defaults for DIRECT and OPEN commands.
TIMEOUT_DEFAULTS = {
    "SET_TOGGLE":    3000,
    "PRESS_BUTTON":  3000,
    "SET_SLIDER":    5000,
    "SET_ENCODER":   6000,
    "SET_ROTARY_SW": 5000,
    "SET_JOYSTICK":  8000,
    "MATCH_COLOR":   8000,
    "ENTER_CODE":    8000,
    "SCAN_NFC":      10000,
    "PLUG_JACK":     6000,
    "SET_TRIGGER":   5000,
}

# Cooperative commands need extra time for cross-player verbal relay.
COOP_TIMEOUT_DEFAULTS = {
    "SET_TOGGLE":    5000,
    "PRESS_BUTTON":  5000,
    "SET_SLIDER":    8000,
    "SET_ENCODER":   8000,
    "SET_ROTARY_SW": 8000,
    "SET_JOYSTICK":  12000,
    "MATCH_COLOR":   12000,
    "ENTER_CODE":    12000,
    "SCAN_NFC":      12000,
    "PLUG_JACK":     8000,
    "SET_TRIGGER":   8000,
}

# ──────────────────────────────────────────────────────────────────────
# PREFLIGHT_DEFAULTS
# ──────────────────────────────────────────────────────────────────────
# Default "home" positions for stateful actions.
PREFLIGHT_DEFAULTS = {
    "SET_TOGGLE":    False,
    "SET_SLIDER":    0,
    "SET_TRIGGER":   0,
    "SET_ROTARY_SW": 1,
    "PLUG_JACK":     {"A": "1", "B": "2", "C": "3"},
}
