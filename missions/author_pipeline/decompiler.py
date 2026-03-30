"""Decompiler: materialized runtime JSON → source format (.src.json).

Takes an existing (validated) scenario and produces the leaner source
representation, replacing concrete action/slot/value/tolerance/tier/timeout
with capability references and value presets wherever possible.

Round-trip guarantee: decompile(original) → compile → should equal the
original (semantic equality, ignoring field ordering).
"""

import copy

from missions.validate.capability_matrix import CAPABILITY_MATRIX, TIER_ACTIONS

from .presets import (
    COOP_TIMEOUT_DEFAULTS,
    TIMEOUT_DEFAULTS,
    TOLERANCE_DEFAULTS,
    VALUE_PRESETS,
)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _values_equal(a, b):
    """Deep equality for JSON-compatible values (handles None, bool, int edge cases)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    # Distinguish bool from int (JSON true ≠ 1)
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    return a == b


def _resolve_tier(action):
    for tier, actions in TIER_ACTIONS.items():
        if action in actions:
            return tier
    return None


def _find_preset(action, value, tolerance):
    """Find a VALUE_PRESETS entry matching value (and optionally tolerance).

    Returns (preset_name, full_match) where full_match is True if the
    preset also accounts for tolerance (so tolerance can be omitted).
    """
    presets = VALUE_PRESETS.get(action, {})
    for name, preset in presets.items():
        if not _values_equal(preset["value"], value):
            continue
        preset_tol = preset.get("tolerance")
        if preset_tol is not None:
            if _values_equal(preset_tol, tolerance):
                return name, True   # value + tolerance covered
            else:
                return name, False  # value matches, tolerance doesn't
        else:
            # Preset has no tolerance — value-only match
            return name, True
    return None, False


# ──────────────────────────────────────────────────────────────────────
# Per-pool decompilers
# ──────────────────────────────────────────────────────────────────────

def _decompile_direct_command(cmd):
    action = cmd["action"]
    value = cmd.get("value")
    tolerance = cmd.get("tolerance")

    out = {
        "id": cmd["id"],
        "target_arch": cmd["target_arch"],
        "capability": cmd["slot"],
        "label": cmd["label"],
        "narrator_line": cmd["narrator_line"],
    }

    preset_name, tol_covered = _find_preset(action, value, tolerance)
    if preset_name:
        out["value_preset"] = preset_name
        if not tol_covered and tolerance is not None:
            out["tolerance"] = tolerance
    else:
        out["value"] = value
        if tolerance is not None:
            default_tol = TOLERANCE_DEFAULTS.get(action)
            if not _values_equal(tolerance, default_tol):
                out["tolerance"] = tolerance

    # Omit tier if it matches the derived default
    expected_tier = _resolve_tier(action)
    if cmd.get("tier") and cmd["tier"] != expected_tier:
        out["tier"] = cmd["tier"]

    # Omit timeout if it matches the default
    default_timeout = TIMEOUT_DEFAULTS.get(action)
    if cmd.get("timeout_ms") is not None and cmd["timeout_ms"] != default_timeout:
        out["timeout_ms"] = cmd["timeout_ms"]

    return out


def _decompile_coop_command(cmd):
    action = cmd["action"]
    value = cmd.get("value")
    tolerance = cmd.get("tolerance")

    out = {
        "id": cmd["id"],
        "display_on": cmd["display_on"],
        "target_arch": cmd["target_arch"],
        "capability": cmd["slot"],
        "label": cmd["label"],
        "narrator_line": cmd["narrator_line"],
    }

    preset_name, tol_covered = _find_preset(action, value, tolerance)
    if preset_name:
        out["value_preset"] = preset_name
        if not tol_covered and tolerance is not None:
            out["tolerance"] = tolerance
    else:
        out["value"] = value
        if tolerance is not None:
            default_tol = TOLERANCE_DEFAULTS.get(action)
            if not _values_equal(tolerance, default_tol):
                out["tolerance"] = tolerance

    expected_tier = _resolve_tier(action)
    if cmd.get("tier") and cmd["tier"] != expected_tier:
        out["tier"] = cmd["tier"]

    default_timeout = COOP_TIMEOUT_DEFAULTS.get(action)
    if cmd.get("timeout_ms") is not None and cmd["timeout_ms"] != default_timeout:
        out["timeout_ms"] = cmd["timeout_ms"]

    return out


def _decompile_open_command(cmd):
    action = cmd["action"]
    value = cmd.get("value")
    tolerance = cmd.get("tolerance")

    out = {
        "id": cmd["id"],
        "target": "ANY",
        "action": action,
        "label": cmd["label"],
        "narrator_line": cmd["narrator_line"],
    }

    preset_name, tol_covered = _find_preset(action, value, tolerance)
    if preset_name:
        out["value_preset"] = preset_name
        if not tol_covered and tolerance is not None:
            out["tolerance"] = tolerance
    else:
        out["value"] = value
        if tolerance is not None:
            default_tol = TOLERANCE_DEFAULTS.get(action)
            if not _values_equal(tolerance, default_tol):
                out["tolerance"] = tolerance

    expected_tier = _resolve_tier(action)
    if cmd.get("tier") and cmd["tier"] != expected_tier:
        out["tier"] = cmd["tier"]

    default_timeout = TIMEOUT_DEFAULTS.get(action)
    if cmd.get("timeout_ms") is not None and cmd["timeout_ms"] != default_timeout:
        out["timeout_ms"] = cmd["timeout_ms"]

    return out


def _decompile_crisis_action(action_entry):
    if "rest" in action_entry:
        return dict(action_entry)

    target_arch = action_entry["target_arch"]
    action = action_entry["action"]
    value = action_entry.get("value")
    tolerance = action_entry.get("tolerance")

    out = {
        "target_arch": target_arch,
        "capability": action_entry["slot"],
    }

    preset_name, tol_covered = _find_preset(action, value, tolerance)
    if preset_name:
        out["value_preset"] = preset_name
        if not tol_covered and tolerance is not None:
            out["tolerance"] = tolerance
    else:
        out["value"] = value
        if tolerance is not None:
            default_tol = TOLERANCE_DEFAULTS.get(action)
            if not _values_equal(tolerance, default_tol):
                out["tolerance"] = tolerance

    return out


def _decompile_preflight(init_commands):
    compiled = {}
    for arch, cmds in init_commands.items():
        decompiled_cmds = []
        for cmd in cmds:
            slot = cmd["slot"]
            action = cmd["action"]
            value = cmd.get("value")

            entry = {"capability": slot}

            preset_name, _ = _find_preset(action, value, None)
            if preset_name:
                entry["value_preset"] = preset_name
            else:
                entry["value"] = value

            decompiled_cmds.append(entry)
        compiled[arch] = decompiled_cmds
    return compiled


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def decompile_scenario(materialized):
    """Convert a materialized scenario dict into source format.

    The input is not mutated; a new dict is returned.
    """
    out = copy.deepcopy(materialized)

    # ── Command pools ──
    pools = out.get("command_pools", {})
    if "direct" in pools:
        pools["direct"] = [_decompile_direct_command(c) for c in pools["direct"]]
    if "cooperative" in pools:
        pools["cooperative"] = [_decompile_coop_command(c) for c in pools["cooperative"]]
    if "open" in pools:
        pools["open"] = [_decompile_open_command(c) for c in pools["open"]]

    # ── Crises ──
    for crisis in out.get("crises", []):
        if "actions" in crisis:
            crisis["actions"] = [
                _decompile_crisis_action(a) for a in crisis["actions"]
            ]

    # ── Preflight init_commands ──
    for phase in out.get("phases", []):
        if phase.get("type") == "PREFLIGHT" and "init_commands" in phase:
            phase["init_commands"] = _decompile_preflight(
                phase["init_commands"]
            )

    return out
