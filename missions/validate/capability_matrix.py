"""Hardware truth tables for Spaceteam IRL tablet archetypes.

These mappings are the single source of truth for which physical controls
exist on each tablet archetype and what action types they support.
Derived from docs/tablet-archetypes.md and docs/scenario-schema.md.

Layout (every tablet):
  Universal base — 3 toggle switches, 4 momentary buttons, 1 crisis button, 1 submit button
  Specialty elements — 2 per archetype, drawn from a pool of 9 unique elements

Slot naming:
  toggle_1 / toggle_2 / toggle_3          — universal toggles (bat / rocker / paddle)
  button_1 / button_2 / button_3 / button_4  — universal momentary (round-red / square-blue / oval-yellow / diamond-green)
  specialty_a / specialty_b               — archetype-specific elements
  crisis / submit                         — always present, not scenario-commanded (crisis is event-driven)
"""

ARCHETYPES = [
    "NAVIGATOR", "ENGINEER", "OPERATOR", "SENTINEL",
    "MEDIC", "ANALYST", "SCOUT", "COMMANDER",
]

# ──────────────────────────────────────────────────────────────────────
# Specialty Element Pool (9 elements)
# ──────────────────────────────────────────────────────────────────────
#   JOYSTICK         — Navigator, Scout
#   SLIDER           — Navigator, Engineer
#   BARREL_JACKS     — Engineer, Commander
#   ROTARY_ENCODER   — Operator, Medic
#   NUMBER_PAD       — Operator, Analyst
#   HALL_TRIGGER     — Sentinel
#   NFC_SCANNER      — Commander
#   ROTARY_SWITCH    — Sentinel, Analyst
#   COLOR_DIAL       — Medic, Scout
# ──────────────────────────────────────────────────────────────────────

# Maps archetype -> slot -> action type supported by that physical control.
# Universal slots use the same names on every tablet.
# Specialty slots (specialty_a, specialty_b) vary by archetype.
CAPABILITY_MATRIX = {
    "NAVIGATOR": {
        "toggle_1":    "SET_TOGGLE",      # Bat toggle
        "toggle_2":    "SET_TOGGLE",      # Rocker toggle
        "toggle_3":    "SET_TOGGLE",      # Paddle toggle
        "button_1":    "PRESS_BUTTON",    # Round red
        "button_2":    "PRESS_BUTTON",    # Square blue
        "button_3":    "PRESS_BUTTON",    # Oval yellow
        "button_4":    "PRESS_BUTTON",    # Diamond green
        "specialty_a": "SET_JOYSTICK",    # Joystick (2-axis ADC + click)
        "specialty_b": "SET_SLIDER",      # Linear Slider / Fader (ADC)
    },
    "ENGINEER": {
        "toggle_1":    "SET_TOGGLE",
        "toggle_2":    "SET_TOGGLE",
        "toggle_3":    "SET_TOGGLE",
        "button_1":    "PRESS_BUTTON",
        "button_2":    "PRESS_BUTTON",
        "button_3":    "PRESS_BUTTON",
        "button_4":    "PRESS_BUTTON",
        "specialty_a": "SET_SLIDER",      # Linear Slider / Fader (ADC)
        "specialty_b": "PLUG_JACK",       # Barrel Jack Patch Bay (3 ports, 3 wires)
    },
    "OPERATOR": {
        "toggle_1":    "SET_TOGGLE",
        "toggle_2":    "SET_TOGGLE",
        "toggle_3":    "SET_TOGGLE",
        "button_1":    "PRESS_BUTTON",
        "button_2":    "PRESS_BUTTON",
        "button_3":    "PRESS_BUTTON",
        "button_4":    "PRESS_BUTTON",
        "specialty_a": "SET_ENCODER",     # Rotary Encoder (A/B + click)
        "specialty_b": "ENTER_CODE",      # 4-Button Number Pad
    },
    "SENTINEL": {
        "toggle_1":    "SET_TOGGLE",
        "toggle_2":    "SET_TOGGLE",
        "toggle_3":    "SET_TOGGLE",
        "button_1":    "PRESS_BUTTON",
        "button_2":    "PRESS_BUTTON",
        "button_3":    "PRESS_BUTTON",
        "button_4":    "PRESS_BUTTON",
        "specialty_a": "SET_TRIGGER",     # Hall-Effect Analog Trigger (spring-return lever)
        "specialty_b": "SET_ROTARY_SW",   # 6-Position Rotary Switch (ADC ladder)
    },
    "MEDIC": {
        "toggle_1":    "SET_TOGGLE",
        "toggle_2":    "SET_TOGGLE",
        "toggle_3":    "SET_TOGGLE",
        "button_1":    "PRESS_BUTTON",
        "button_2":    "PRESS_BUTTON",
        "button_3":    "PRESS_BUTTON",
        "button_4":    "PRESS_BUTTON",
        "specialty_a": "MATCH_COLOR",     # Color Dial (pot + 2 RGB LEDs)
        "specialty_b": "SET_ENCODER",     # Rotary Encoder (EC11-style)
    },
    "ANALYST": {
        "toggle_1":    "SET_TOGGLE",
        "toggle_2":    "SET_TOGGLE",
        "toggle_3":    "SET_TOGGLE",
        "button_1":    "PRESS_BUTTON",
        "button_2":    "PRESS_BUTTON",
        "button_3":    "PRESS_BUTTON",
        "button_4":    "PRESS_BUTTON",
        "specialty_a": "ENTER_CODE",      # 4-Button Number Pad
        "specialty_b": "SET_ROTARY_SW",   # 6-Position Rotary Switch (ADC ladder)
    },
    "SCOUT": {
        "toggle_1":    "SET_TOGGLE",
        "toggle_2":    "SET_TOGGLE",
        "toggle_3":    "SET_TOGGLE",
        "button_1":    "PRESS_BUTTON",
        "button_2":    "PRESS_BUTTON",
        "button_3":    "PRESS_BUTTON",
        "button_4":    "PRESS_BUTTON",
        "specialty_a": "SET_JOYSTICK",    # Joystick (2-axis ADC + click)
        "specialty_b": "MATCH_COLOR",     # Color Dial (pot + 2 RGB LEDs)
    },
    "COMMANDER": {
        "toggle_1":    "SET_TOGGLE",
        "toggle_2":    "SET_TOGGLE",
        "toggle_3":    "SET_TOGGLE",
        "button_1":    "PRESS_BUTTON",
        "button_2":    "PRESS_BUTTON",
        "button_3":    "PRESS_BUTTON",
        "button_4":    "PRESS_BUTTON",
        "specialty_a": "PLUG_JACK",       # Barrel Jack Patch Bay (3 ports, 3 wires)
        "specialty_b": "SCAN_NFC",        # NFC/RFID Scanner RC522 (SPI)
    },
}

# ──────────────────────────────────────────────────────────────────────
# Slot Classification
# ──────────────────────────────────────────────────────────────────────
UNIVERSAL_SLOTS = [
    "toggle_1", "toggle_2", "toggle_3",
    "button_1", "button_2", "button_3", "button_4",
]
SPECIALTY_SLOTS = ["specialty_a", "specialty_b"]
ALL_COMMANDABLE_SLOTS = UNIVERSAL_SLOTS + SPECIALTY_SLOTS

# ──────────────────────────────────────────────────────────────────────
# Element → Archetype reverse lookup
# ──────────────────────────────────────────────────────────────────────
ELEMENT_ARCHETYPES = {
    "SET_JOYSTICK":  ["NAVIGATOR", "SCOUT"],
    "SET_SLIDER":    ["NAVIGATOR", "ENGINEER"],
    "PLUG_JACK":     ["ENGINEER", "COMMANDER"],
    "SET_ENCODER":   ["OPERATOR", "MEDIC"],
    "ENTER_CODE":    ["OPERATOR", "ANALYST"],
    "SET_TRIGGER":   ["SENTINEL"],
    "SCAN_NFC":      ["COMMANDER"],
    "SET_ROTARY_SW": ["SENTINEL", "ANALYST"],
    "MATCH_COLOR":   ["MEDIC", "SCOUT"],
}

# ──────────────────────────────────────────────────────────────────────
# Command Complexity Tiers
# ──────────────────────────────────────────────────────────────────────
# T1 = quick binary actions (toggles, button presses)
# T2 = moderate precision (slider, encoder, rotary switch, patch bay)
# T3 = high complexity (joystick 2-axis, color matching, code entry, NFC scan)
TIER_ACTIONS = {
    "T1": {"SET_TOGGLE", "PRESS_BUTTON"},
    "T2": {"SET_SLIDER", "SET_ENCODER", "SET_ROTARY_SW", "PLUG_JACK", "SET_TRIGGER"},
    "T3": {"SET_JOYSTICK", "MATCH_COLOR", "ENTER_CODE", "SCAN_NFC"},
}

# Timeout ranges (ms) per tier.
TIER_TIMEOUT_RANGE = {
    "T1": (2000, 5000),
    "T2": (3000, 8000),
    "T3": (5000, 12000),
}

# All valid action types (union of all tiers).
ALL_ACTIONS = TIER_ACTIONS["T1"] | TIER_ACTIONS["T2"] | TIER_ACTIONS["T3"]

# ──────────────────────────────────────────────────────────────────────
# Stateful vs Momentary Controls
# ──────────────────────────────────────────────────────────────────────
# Stateful controls retain their position — the Hub must track state
# and only issue valid commands (e.g., don't command "turn ON" if already ON).
# Scenario command pools MUST provide both ON and OFF variants for binary
# stateful actions, and multiple target values for continuous stateful actions.
STATEFUL_ACTIONS = {
    "SET_TOGGLE",       # binary: on / off
    "PLUG_JACK",        # binary per-port: wire-in / wire-out (tracked per port)
    "SET_SLIDER",       # continuous: 0–100
    "SET_TRIGGER",      # continuous: 0–100 (spring-return to 0)
    "SET_ENCODER",      # continuous: integer position
    "SET_ROTARY_SW",    # discrete: 1–6
    "MATCH_COLOR",      # continuous: [r, g, b]
}

# Momentary controls are fire-and-forget — no state tracking needed.
MOMENTARY_ACTIONS = {
    "PRESS_BUTTON",     # momentary push
    "ENTER_CODE",       # sequence entry (resets after submit)
    "SCAN_NFC",         # tap-to-scan (event, not state)
}

# Binary stateful actions that MUST have both true/false values in pools.
BINARY_STATEFUL_ACTIONS = {"SET_TOGGLE"}

# ──────────────────────────────────────────────────────────────────────
# Crisis Event Types
# ──────────────────────────────────────────────────────────────────────
CRISIS_TYPES = {"CRISIS_ALL", "CRISIS_THRESHOLD", "MULTI_ACTION"}

# Crisis penalty types.
CRISIS_PENALTIES = {"health_minor", "health_major"}

# Outcome tiers.
OUTCOME_TIERS = {"TRIUMPH", "SUCCESS", "SURVIVE", "FAILURE", "DISASTER"}

# ──────────────────────────────────────────────────────────────────────
# Branch Structure
# ──────────────────────────────────────────────────────────────────────
# All 8 branch paths (Win/Lose across 3 branch points).
BRANCH_PATHS = ["WWW", "WWL", "WLW", "WLL", "LWW", "LWL", "LLW", "LLL"]

# Required frantic phase IDs (3 branch → 7 frantic phases).
FRANTIC_PHASE_IDS = [
    "frantic_1",
    "frantic_2_W", "frantic_2_L",
    "frantic_3_WW", "frantic_3_WL", "frantic_3_LW", "frantic_3_LL",
]

# Which frantic phases each path traverses.
PATH_PHASES = {
    "WWW": ["frantic_1", "frantic_2_W", "frantic_3_WW"],
    "WWL": ["frantic_1", "frantic_2_W", "frantic_3_WW"],
    "WLW": ["frantic_1", "frantic_2_W", "frantic_3_WL"],
    "WLL": ["frantic_1", "frantic_2_W", "frantic_3_WL"],
    "LWW": ["frantic_1", "frantic_2_L", "frantic_3_LW"],
    "LWL": ["frantic_1", "frantic_2_L", "frantic_3_LW"],
    "LLW": ["frantic_1", "frantic_2_L", "frantic_3_LL"],
    "LLL": ["frantic_1", "frantic_2_L", "frantic_3_LL"],
}

# ──────────────────────────────────────────────────────────────────────
# Label & Pool Constraints
# ──────────────────────────────────────────────────────────────────────
# OLED labels: one per commandable slot (7 universal + 2 specialty = 9)
OLED_LABEL_COUNT = 9
OLED_LABEL_MAX = 16
SCREEN_LABEL_MAX = 40
NARRATOR_LINE_MAX = 200

# Pool coverage minimums.
MIN_DIRECT_PER_ARCH = 5
MIN_COOP_PER_ARCH = 2

# Minimum crises per scenario.
MIN_CRISES = 2

# ──────────────────────────────────────────────────────────────────────
# Command Targeting Modes
# ──────────────────────────────────────────────────────────────────────
# TARGETED  — command for a specific archetype (target_arch = "NAVIGATOR")
# OPEN      — any archetype with the right element can answer (target = "ANY")
#             First correct responder wins; others get cooperative green flash.
# COOP      — displayed on one player's screen, executed by another
COMMAND_MODES = {"TARGETED", "OPEN", "COOP"}


# ──────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────

def get_tier(action):
    """Return the tier (T1/T2/T3) for a given action type, or None."""
    for tier, actions in TIER_ACTIONS.items():
        if action in actions:
            return tier
    return None


def get_valid_actions(archetype):
    """Return {slot: action_type} for an archetype."""
    return CAPABILITY_MATRIX.get(archetype, {})


def is_valid_command(archetype, action, slot):
    """Check if an archetype can perform this action on this slot."""
    return CAPABILITY_MATRIX.get(archetype, {}).get(slot) == action


def get_archetypes_for_action(action):
    """Return list of archetypes that have this action on any slot."""
    result = []
    for arch, slots in CAPABILITY_MATRIX.items():
        if action in slots.values():
            result.append(arch)
    return result


def get_slot_for_action(archetype, action):
    """Return the slot name where an archetype has this action, or None."""
    for slot, act in CAPABILITY_MATRIX.get(archetype, {}).items():
        if act == action:
            return slot
    return None


def is_stateful(action):
    """Return True if the action type tracks persistent state."""
    return action in STATEFUL_ACTIONS


def is_specialty_slot(slot):
    """Return True if the slot is a specialty element (not universal base)."""
    return slot in ("specialty_a", "specialty_b")
