"""Compiler: source-format scenario (.src.json) → materialized runtime JSON.

The source format lets authors write commands using semantic capability
references and named value presets.  The compiler resolves everything into
the concrete action/slot/value/tolerance/tier/timeout fields the Hub
firmware expects.
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
# Internal helpers
# ──────────────────────────────────────────────────────────────────────

def _resolve_action(target_arch, capability):
    """Look up the action type for a capability (slot) on a given archetype."""
    arch_caps = CAPABILITY_MATRIX.get(target_arch)
    if arch_caps is None:
        raise ValueError(f"Unknown archetype: {target_arch}")
    action = arch_caps.get(capability)
    if action is None:
        raise ValueError(
            f"Archetype {target_arch} has no capability '{capability}'"
        )
    return action


def _resolve_tier(action):
    """Derive the command tier from the action type."""
    for tier, actions in TIER_ACTIONS.items():
        if action in actions:
            return tier
    raise ValueError(f"Action {action} not found in any tier")


def _resolve_value(action, cmd):
    """Resolve value and tolerance from a preset name or raw value.

    Returns (value, tolerance_or_None).
    """
    if "value_preset" in cmd:
        preset_name = cmd["value_preset"]
        presets = VALUE_PRESETS.get(action, {})
        preset = presets.get(preset_name)
        if preset is None:
            raise ValueError(
                f"Unknown value preset '{preset_name}' for action {action}. "
                f"Available: {list(presets.keys())}"
            )
        return preset["value"], preset.get("tolerance")

    if "value" in cmd:
        return cmd["value"], cmd.get("tolerance")

    raise ValueError(
        f"Command '{cmd.get('id', '?')}' has neither 'value_preset' nor 'value'"
    )


# ──────────────────────────────────────────────────────────────────────
# Per-pool compilers
# ──────────────────────────────────────────────────────────────────────

def _pick_tolerance(cmd_tolerance, preset_tolerance, action):
    """Choose tolerance with priority: explicit > preset > default."""
    if cmd_tolerance is not None:
        return cmd_tolerance
    if preset_tolerance is not None:
        return preset_tolerance
    return TOLERANCE_DEFAULTS.get(action)


def _compile_direct_command(cmd):
    target_arch = cmd["target_arch"]
    capability = cmd["capability"]
    action = _resolve_action(target_arch, capability)
    tier = cmd.get("tier") or _resolve_tier(action)
    value, preset_tol = _resolve_value(action, cmd)

    tolerance = _pick_tolerance(cmd.get("tolerance"), preset_tol, action)
    timeout = cmd.get("timeout_ms")
    if timeout is None:
        timeout = TIMEOUT_DEFAULTS.get(action)

    out = {
        "id": cmd["id"],
        "target_arch": target_arch,
        "action": action,
        "slot": capability,
        "tier": tier,
        "label": cmd["label"],
        "narrator_line": cmd["narrator_line"],
        "value": value,
    }
    if tolerance is not None:
        out["tolerance"] = tolerance
    if timeout is not None:
        out["timeout_ms"] = timeout
    return out


def _compile_coop_command(cmd):
    target_arch = cmd["target_arch"]
    capability = cmd["capability"]
    action = _resolve_action(target_arch, capability)
    tier = cmd.get("tier") or _resolve_tier(action)
    value, preset_tol = _resolve_value(action, cmd)

    tolerance = _pick_tolerance(cmd.get("tolerance"), preset_tol, action)
    timeout = cmd.get("timeout_ms")
    if timeout is None:
        timeout = COOP_TIMEOUT_DEFAULTS.get(action)

    out = {
        "id": cmd["id"],
        "display_on": cmd["display_on"],
        "target_arch": target_arch,
        "action": action,
        "slot": capability,
        "tier": tier,
        "label": cmd["label"],
        "narrator_line": cmd["narrator_line"],
        "value": value,
    }
    if tolerance is not None:
        out["tolerance"] = tolerance
    if timeout is not None:
        out["timeout_ms"] = timeout
    return out


def _compile_open_command(cmd):
    # Open commands keep "action" (no archetype to derive from).
    action = cmd["action"]
    tier = cmd.get("tier") or _resolve_tier(action)
    value, preset_tol = _resolve_value(action, cmd)

    tolerance = _pick_tolerance(cmd.get("tolerance"), preset_tol, action)
    timeout = cmd.get("timeout_ms")
    if timeout is None:
        timeout = TIMEOUT_DEFAULTS.get(action)

    out = {
        "id": cmd["id"],
        "target": "ANY",
        "action": action,
        "tier": tier,
        "label": cmd["label"],
        "narrator_line": cmd["narrator_line"],
        "value": value,
    }
    if tolerance is not None:
        out["tolerance"] = tolerance
    if timeout is not None:
        out["timeout_ms"] = timeout
    return out


def _compile_crisis_action(action_entry):
    """Compile one entry in a crisis's ``actions`` array."""
    if "rest" in action_entry:
        return dict(action_entry)  # {"rest": "CRISIS_BTN"} passes through

    target_arch = action_entry["target_arch"]
    capability = action_entry["capability"]
    action = _resolve_action(target_arch, capability)
    value, preset_tol = _resolve_value(action, action_entry)

    tolerance = _pick_tolerance(
        action_entry.get("tolerance"), preset_tol, action
    )

    out = {
        "target_arch": target_arch,
        "action": action,
        "slot": capability,
        "value": value,
    }
    if tolerance is not None:
        out["tolerance"] = tolerance
    return out


def _compile_preflight(init_commands):
    """Compile the ``preflight.init_commands`` block."""
    compiled = {}
    for arch, cmds in init_commands.items():
        compiled_cmds = []
        for cmd in cmds:
            capability = cmd["capability"]
            action = _resolve_action(arch, capability)

            if "value_preset" in cmd:
                presets = VALUE_PRESETS.get(action, {})
                preset = presets.get(cmd["value_preset"])
                if preset is None:
                    raise ValueError(
                        f"Unknown preflight preset '{cmd['value_preset']}' "
                        f"for {arch}.{capability} ({action})"
                    )
                value = preset["value"]
            else:
                value = cmd["value"]

            compiled_cmds.append({
                "slot": capability,
                "action": action,
                "value": value,
            })
        compiled[arch] = compiled_cmds
    return compiled


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def compile_scenario(source):
    """Compile a source-format scenario dict into materialized format.

    The source dict is not mutated; a new dict is returned.
    """
    out = copy.deepcopy(source)

    # ── Command pools ──
    pools = out.get("command_pools", {})
    if "direct" in pools:
        pools["direct"] = [_compile_direct_command(c) for c in pools["direct"]]
    if "cooperative" in pools:
        pools["cooperative"] = [_compile_coop_command(c) for c in pools["cooperative"]]
    if "open" in pools:
        pools["open"] = [_compile_open_command(c) for c in pools["open"]]

    # ── Crises ──
    for crisis in out.get("crises", []):
        if "actions" in crisis:
            crisis["actions"] = [
                _compile_crisis_action(a) for a in crisis["actions"]
            ]

    # ── Preflight init_commands ──
    for phase in out.get("phases", []):
        if phase.get("type") == "PREFLIGHT" and "init_commands" in phase:
            phase["init_commands"] = _compile_preflight(phase["init_commands"])

    return out
