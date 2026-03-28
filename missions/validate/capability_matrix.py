"""Hardware truth tables for Spaceteam IRL tablet archetypes.

These mappings are the single source of truth for which physical controls
exist on each tablet archetype and what action types they support.
Derived from docs/tablet-archetypes.md and docs/scenario-schema.md.
"""

ARCHETYPES = [
    "NAVIGATOR", "ENGINEER", "OPERATOR", "SENTINEL",
    "MEDIC", "ANALYST", "SCOUT", "COMMANDER",
]

# Maps archetype -> slot -> action type supported by that physical control.
# Slot 1 = Signature control, Slot 2 = Medium control, Slots 3-5 = Simple controls.
CAPABILITY_MATRIX = {
    "NAVIGATOR": {
        1: "SET_JOYSTICK",    # Analog Joystick (2-axis ADC + click)
        2: "SET_SLIDER",      # Linear Slider 45mm (ADC)
        3: "SET_TOGGLE",      # Toggle
        4: "SET_TOGGLE",      # Toggle
        5: "PRESS_BUTTON",    # Momentary Pushbutton
    },
    "ENGINEER": {
        1: "SET_SLIDER",      # Linear Slider 60mm (ADC)
        2: "PRESS_BUTTON",    # Illuminated Arcade Button
        3: "SET_TOGGLE",      # Toggle
        4: "SET_TOGGLE",      # Toggle
        5: "SET_TOGGLE",      # Toggle
    },
    "OPERATOR": {
        1: "SET_ENCODER",     # Rotary Encoder (A/B + click)
        2: "SET_TOGGLE",      # Covered Safety Toggle
        3: "SET_TOGGLE",      # Toggle
        4: "PRESS_BUTTON",    # Momentary
        5: "PRESS_BUTTON",    # Momentary
    },
    "SENTINEL": {
        1: "SCAN_NFC",        # NFC/RFID Scanner RC522 (SPI)
        2: "SET_ROTARY_SW",   # 3-Position Rotary Switch (ADC ladder)
        3: "SET_TOGGLE",      # Toggle
        4: "SET_TOGGLE",      # Toggle
        5: "PRESS_BUTTON",    # Momentary
    },
    "MEDIC": {
        1: "MATCH_COLOR",     # Color-Match Dial (ADC pot + NeoPixel)
        2: "SET_ENCODER",     # Rotary Encoder (small, EC11-style)
        3: "SET_TOGGLE",      # Toggle
        4: "PRESS_BUTTON",    # Momentary
        5: "PRESS_BUTTON",    # Momentary
    },
    "ANALYST": {
        1: "ENTER_CODE",      # 4-Button Keypad
        2: "MATCH_WAVE",      # LED Wave Dial (small pot + 4-LED bar)
        3: "SET_TOGGLE",      # Toggle
        4: "SET_TOGGLE",      # Toggle
        5: "PRESS_BUTTON",    # Momentary
    },
    "SCOUT": {
        1: "MATCH_WAVE",      # LED Wave Dial (ADC pot + NeoPixel ring)
        2: "SET_TOGGLE",      # Covered Safety Toggle
        3: "SET_TOGGLE",      # Toggle
        4: "SET_TOGGLE",      # Toggle
        5: "SET_TOGGLE",      # Toggle
    },
    "COMMANDER": {
        1: "SET_ROTARY_SW",   # Multi-Position Rotary Switch 6-pos (ADC ladder)
        2: "PRESS_BUTTON",    # Illuminated Arcade Button
        3: "SET_TOGGLE",      # Toggle
        4: "PRESS_BUTTON",    # Momentary
        5: "PRESS_BUTTON",    # Momentary
    },
}

# Command complexity tiers: action -> human effort required.
TIER_ACTIONS = {
    "T1": {"SET_TOGGLE", "PRESS_BUTTON"},
    "T2": {"SET_SLIDER", "SET_ENCODER", "SET_ROTARY_SW", "MATCH_WAVE"},
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

# Crisis event types.
CRISIS_TYPES = {"CRISIS_ALL", "CRISIS_THRESHOLD", "MULTI_ACTION"}

# Crisis penalty types.
CRISIS_PENALTIES = {"health_minor", "health_major"}

# Outcome tiers.
OUTCOME_TIERS = {"TRIUMPH", "SUCCESS", "SURVIVE", "FAILURE", "DISASTER"}

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

# Label length limits.
OLED_LABEL_MAX = 16
SCREEN_LABEL_MAX = 40
NARRATOR_LINE_MAX = 200

# Pool coverage minimums.
MIN_DIRECT_PER_ARCH = 5
MIN_COOP_PER_ARCH = 2

# Minimum crises per scenario.
MIN_CRISES = 2


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
