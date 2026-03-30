"""Scenario JSON validator for Spaceteam IRL.

Checks every rule from docs/scenario-schema.md against a loaded scenario dict.
"""

import json
from pathlib import Path

from .capability_matrix import (
    ARCHETYPES, CAPABILITY_MATRIX, TIER_ACTIONS, TIER_TIMEOUT_RANGE,
    ALL_ACTIONS, ALL_COMMANDABLE_SLOTS, ELEMENT_ARCHETYPES,
    STATEFUL_ACTIONS, BINARY_STATEFUL_ACTIONS,
    CRISIS_TYPES, CRISIS_PENALTIES, OUTCOME_TIERS,
    BRANCH_PATHS, FRANTIC_PHASE_IDS,
    OLED_LABEL_COUNT, OLED_LABEL_MAX, SCREEN_LABEL_MAX, NARRATOR_LINE_MAX,
    MIN_DIRECT_PER_ARCH, MIN_COOP_PER_ARCH, MIN_CRISES,
    get_tier, is_valid_command,
)
from .difficulty_presets import DIFFICULTY_LEVELS, PRESETS


class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, rule, msg):
        self.errors.append((rule, msg))

    def warn(self, rule, msg):
        self.warnings.append((rule, msg))

    @property
    def passed(self):
        return len(self.errors) == 0

    def summary(self):
        lines = []
        if self.errors:
            lines.append(f"\n{'='*60}")
            lines.append(f"ERRORS ({len(self.errors)})")
            lines.append(f"{'='*60}")
            for rule, msg in self.errors:
                lines.append(f"  [{rule}] {msg}")
        if self.warnings:
            lines.append(f"\n{'='*60}")
            lines.append(f"WARNINGS ({len(self.warnings)})")
            lines.append(f"{'='*60}")
            for rule, msg in self.warnings:
                lines.append(f"  [{rule}] {msg}")
        status = "PASS" if self.passed else "FAIL"
        lines.append(f"\n{'='*60}")
        lines.append(f"RESULT: {status}  ({len(self.errors)} errors, {len(self.warnings)} warnings)")
        lines.append(f"{'='*60}")
        return "\n".join(lines)


def validate(scenario):
    """Run all validation checks on a scenario dict."""
    r = ValidationResult()
    _check_meta(scenario, r)
    _check_roles(scenario, r)
    _check_oled_labels(scenario, r)
    _check_direct_commands(scenario, r)
    _check_coop_commands(scenario, r)
    _check_open_commands(scenario, r)
    _check_statefulness(scenario, r)
    _check_pool_coverage(scenario, r)
    _check_unique_ids(scenario, r)
    _check_crises(scenario, r)
    _check_phases(scenario, r)
    _check_outcomes(scenario, r)
    _check_narrator(scenario, r)
    return r


def validate_file(path):
    """Load and validate a scenario JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        scenario = json.load(f)
    return scenario, validate(scenario)


# ─── Individual Check Functions ──────────────────────────────────────

def _check_meta(s, r):
    meta = s.get("meta")
    if not meta:
        r.error("META", "Missing 'meta' section")
        return
    for field in ("id", "title", "pack", "difficulty", "player_count", "duration_sec"):
        if field not in meta:
            r.error("META", f"Missing meta.{field}")

    diff = meta.get("difficulty")
    if diff and diff not in DIFFICULTY_LEVELS:
        r.warn("META", f"Difficulty '{diff}' is not a standard preset "
               f"({', '.join(DIFFICULTY_LEVELS)}). "
               f"Custom difficulties must fully specify per-phase params.")

    pc = meta.get("player_count", {})
    if pc.get("min", 0) < 2:
        r.warn("META", "player_count.min < 2 seems low for a cooperative game")
    if pc.get("max", 0) > 8:
        r.error("META", "player_count.max > 8 exceeds hardware limit")

    dur = meta.get("duration_sec", {})
    if dur.get("max", 0) > 1200:
        r.warn("META", "duration_sec.max > 1200s (20 min) — may be too long")
    if dur.get("min", 0) < 300:
        r.warn("META", "duration_sec.min < 300s (5 min) — may be too short")


def _check_roles(s, r):
    roles = s.get("roles", {})
    for arch in ARCHETYPES:
        if arch not in roles:
            r.error("ROLES", f"Missing role mapping for {arch}")
    for arch, name in roles.items():
        if arch not in ARCHETYPES:
            r.error("ROLES", f"Unknown archetype in roles: {arch}")
        if len(name) > SCREEN_LABEL_MAX:
            r.error("ROLES", f"Role name '{name}' exceeds {SCREEN_LABEL_MAX} chars")


def _check_oled_labels(s, r):
    labels = s.get("oled_labels", {})
    for arch in ARCHETYPES:
        if arch not in labels:
            r.error("OLED_LABELS", f"Missing OLED labels for {arch}")
            continue
        arch_labels = labels[arch]
        if len(arch_labels) != OLED_LABEL_COUNT:
            r.error("OLED_LABELS",
                    f"{arch} has {len(arch_labels)} labels, "
                    f"expected {OLED_LABEL_COUNT}")
        for i, label in enumerate(arch_labels):
            if len(label) > OLED_LABEL_MAX:
                slot = ALL_COMMANDABLE_SLOTS[i] if i < len(ALL_COMMANDABLE_SLOTS) else f"index_{i}"
                r.error("OLED_LABELS",
                        f"{arch} {slot} label '{label}' "
                        f"exceeds {OLED_LABEL_MAX} chars ({len(label)})")


def _check_direct_commands(s, r):
    for cmd in s.get("command_pools", {}).get("direct", []):
        cid = cmd.get("id", "???")
        arch = cmd.get("target_arch")
        action = cmd.get("action")
        slot = cmd.get("slot")
        tier = cmd.get("tier")

        # Archetype exists
        if arch not in ARCHETYPES:
            r.error("CAPABILITY", f"Direct cmd '{cid}': unknown archetype '{arch}'")
            continue
        # Action exists
        if action not in ALL_ACTIONS:
            r.error("CAPABILITY", f"Direct cmd '{cid}': unknown action '{action}'")
            continue
        # Slot exists
        if slot not in ALL_COMMANDABLE_SLOTS:
            r.error("CAPABILITY",
                    f"Direct cmd '{cid}': unknown slot '{slot}' "
                    f"(valid: {', '.join(ALL_COMMANDABLE_SLOTS)})")
            continue

        # Capability matrix check
        if not is_valid_command(arch, action, slot):
            expected = CAPABILITY_MATRIX.get(arch, {}).get(slot, "NONE")
            r.error("CAPABILITY",
                    f"Direct cmd '{cid}': {arch} {slot} expects "
                    f"'{expected}', got '{action}'")

        # Tier correctness
        expected_tier = get_tier(action)
        if tier != expected_tier:
            r.error("TIER",
                    f"Direct cmd '{cid}': action '{action}' should be "
                    f"tier {expected_tier}, got {tier}")

        # Timeout within tier range
        timeout = cmd.get("timeout_ms", 0)
        if tier and tier in TIER_TIMEOUT_RANGE:
            lo, hi = TIER_TIMEOUT_RANGE[tier]
            if not (lo <= timeout <= hi):
                r.error("TIMEOUT",
                        f"Direct cmd '{cid}': timeout {timeout}ms "
                        f"outside {tier} range [{lo}-{hi}]")

        # Label lengths
        _check_label_lengths(cmd, cid, "Direct", r)


def _check_coop_commands(s, r):
    pairs = set()
    for cmd in s.get("command_pools", {}).get("cooperative", []):
        cid = cmd.get("id", "???")
        display_on = cmd.get("display_on")
        target_arch = cmd.get("target_arch")
        action = cmd.get("action")
        slot = cmd.get("slot")

        if display_on not in ARCHETYPES:
            r.error("COOP", f"Coop cmd '{cid}': unknown display_on archetype '{display_on}'")
        if target_arch not in ARCHETYPES:
            r.error("COOP", f"Coop cmd '{cid}': unknown target_arch '{target_arch}'")
            continue
        if display_on == target_arch:
            r.error("COOP", f"Coop cmd '{cid}': display_on == target_arch ({display_on})")

        if action not in ALL_ACTIONS:
            r.error("CAPABILITY", f"Coop cmd '{cid}': unknown action '{action}'")
            continue
        if slot not in ALL_COMMANDABLE_SLOTS:
            r.error("CAPABILITY",
                    f"Coop cmd '{cid}': unknown slot '{slot}' "
                    f"(valid: {', '.join(ALL_COMMANDABLE_SLOTS)})")
            continue

        # Executor capability check
        if not is_valid_command(target_arch, action, slot):
            expected = CAPABILITY_MATRIX.get(target_arch, {}).get(slot, "NONE")
            r.error("CAPABILITY",
                    f"Coop cmd '{cid}': executor {target_arch} {slot} "
                    f"expects '{expected}', got '{action}'")

        # Timeout check (coop gets +4000ms overhead for communication)
        timeout = cmd.get("timeout_ms", 0)
        tier = get_tier(action)
        if tier and tier in TIER_TIMEOUT_RANGE:
            lo, hi = TIER_TIMEOUT_RANGE[tier]
            coop_hi = hi + 4000
            if timeout < lo or timeout > coop_hi:
                r.warn("TIMEOUT",
                       f"Coop cmd '{cid}': timeout {timeout}ms unusual "
                       f"for {tier} coop range [{lo}-{coop_hi}]")

        pairs.add((display_on, target_arch))

        # Label lengths
        _check_label_lengths(cmd, cid, "Coop", r)

    if len(pairs) < 8:
        r.warn("COOP_DIVERSITY",
               f"Only {len(pairs)} unique shouter->executor pairs "
               f"(recommend >= 8 for variety)")


def _check_open_commands(s, r):
    """Validate OPEN command pool — specialty-only actions, target = ANY."""
    open_cmds = s.get("command_pools", {}).get("open", [])

    for cmd in open_cmds:
        cid = cmd.get("id", "???")
        target = cmd.get("target")
        action = cmd.get("action")
        tier = cmd.get("tier")

        # Target must be "ANY"
        if target != "ANY":
            r.error("OPEN",
                    f"Open cmd '{cid}': target must be 'ANY', got '{target}'")

        # Action must be a specialty action (in ELEMENT_ARCHETYPES)
        if action not in ELEMENT_ARCHETYPES:
            r.error("OPEN",
                    f"Open cmd '{cid}': action '{action}' is not a specialty "
                    f"action. OPEN commands only target specialty elements "
                    f"(shared across 2 archetypes).")
            continue

        # Tier correctness
        expected_tier = get_tier(action)
        if tier != expected_tier:
            r.error("TIER",
                    f"Open cmd '{cid}': action '{action}' should be "
                    f"tier {expected_tier}, got {tier}")

        # Timeout within tier range
        timeout = cmd.get("timeout_ms", 0)
        if tier and tier in TIER_TIMEOUT_RANGE:
            lo, hi = TIER_TIMEOUT_RANGE[tier]
            if not (lo <= timeout <= hi):
                r.error("TIMEOUT",
                        f"Open cmd '{cid}': timeout {timeout}ms "
                        f"outside {tier} range [{lo}-{hi}]")

        # Label lengths
        _check_label_lengths(cmd, cid, "Open", r)


def _check_statefulness(s, r):
    """Validate that binary stateful commands have both ON and OFF variants."""
    direct = s.get("command_pools", {}).get("direct", [])

    # Track (arch, slot, value) for binary stateful actions
    binary_values = {}  # (arch, slot) -> set of values
    for cmd in direct:
        action = cmd.get("action")
        if action not in BINARY_STATEFUL_ACTIONS:
            continue
        arch = cmd.get("target_arch")
        slot = cmd.get("slot")
        value = cmd.get("value")
        key = (arch, slot)
        binary_values.setdefault(key, set())
        if isinstance(value, bool):
            binary_values[key].add(value)

    # Each (arch, slot) that uses a binary stateful action must have both True and False
    for (arch, slot), values in binary_values.items():
        if True not in values:
            r.error("STATEFULNESS",
                    f"{arch} {slot}: missing value=true variant "
                    f"(binary stateful actions need both ON and OFF)")
        if False not in values:
            r.error("STATEFULNESS",
                    f"{arch} {slot}: missing value=false variant "
                    f"(binary stateful actions need both ON and OFF)")


def _check_pool_coverage(s, r):
    pools = s.get("command_pools", {})
    direct = pools.get("direct", [])
    coop = pools.get("cooperative", [])
    open_cmds = pools.get("open", [])

    direct_by_arch = {}
    for cmd in direct:
        direct_by_arch.setdefault(cmd.get("target_arch"), []).append(cmd)

    coop_by_executor = {}
    for cmd in coop:
        coop_by_executor.setdefault(cmd.get("target_arch"), []).append(cmd)

    for arch in ARCHETYPES:
        dc = len(direct_by_arch.get(arch, []))
        cc = len(coop_by_executor.get(arch, []))
        if dc < MIN_DIRECT_PER_ARCH:
            r.error("POOL_COVERAGE",
                    f"{arch}: only {dc} direct commands (need >= {MIN_DIRECT_PER_ARCH})")
        if cc < MIN_COOP_PER_ARCH:
            r.error("POOL_COVERAGE",
                    f"{arch}: only {cc} coop as executor (need >= {MIN_COOP_PER_ARCH})")

    # Overall tier balance across direct + open pools
    tier_counts = {"T1": 0, "T2": 0, "T3": 0}
    for cmd in direct + open_cmds:
        t = cmd.get("tier")
        if t in tier_counts:
            tier_counts[t] += 1
    total = sum(tier_counts.values())
    if total > 0:
        t1_pct = tier_counts["T1"] / total
        t2_pct = tier_counts["T2"] / total
        t3_pct = tier_counts["T3"] / total
        if t1_pct < 0.30:
            r.warn("TIER_BALANCE", f"T1 is only {t1_pct:.0%} of pool (recommend >= 30%)")
        if t2_pct < 0.10:
            r.warn("TIER_BALANCE", f"T2 is only {t2_pct:.0%} of pool (recommend >= 10%)")
        if t3_pct < 0.10:
            r.warn("TIER_BALANCE", f"T3 is only {t3_pct:.0%} of pool (recommend >= 10%)")


def _check_unique_ids(s, r):
    seen = {}
    for cmd in s.get("command_pools", {}).get("direct", []):
        cid = cmd.get("id")
        if cid in seen:
            r.error("UNIQUE_ID", f"Duplicate ID '{cid}' in direct (also in {seen[cid]})")
        else:
            seen[cid] = "direct"
    for cmd in s.get("command_pools", {}).get("cooperative", []):
        cid = cmd.get("id")
        if cid in seen:
            r.error("UNIQUE_ID", f"Duplicate ID '{cid}' in coop (also in {seen[cid]})")
        else:
            seen[cid] = "coop"
    for cmd in s.get("command_pools", {}).get("open", []):
        cid = cmd.get("id")
        if cid in seen:
            r.error("UNIQUE_ID", f"Duplicate ID '{cid}' in open (also in {seen[cid]})")
        else:
            seen[cid] = "open"
    for crisis in s.get("crises", []):
        cid = crisis.get("id")
        if cid in seen:
            r.error("UNIQUE_ID", f"Duplicate ID '{cid}' in crises (also in {seen[cid]})")
        else:
            seen[cid] = "crises"


def _check_crises(s, r):
    crises = s.get("crises", [])
    if len(crises) < MIN_CRISES:
        r.error("CRISES", f"Only {len(crises)} crises (need >= {MIN_CRISES})")

    for crisis in crises:
        cid = crisis.get("id", "???")
        ctype = crisis.get("type")
        if ctype not in CRISIS_TYPES:
            r.error("CRISES", f"Crisis '{cid}': unknown type '{ctype}'")

        if ctype == "CRISIS_THRESHOLD":
            count = crisis.get("required_count")
            if not isinstance(count, int) or count < 1:
                r.error("CRISES",
                        f"Crisis '{cid}': CRISIS_THRESHOLD needs integer required_count >= 1")

        if ctype == "MULTI_ACTION":
            actions = crisis.get("actions", [])
            if len(actions) < 2:
                r.error("CRISES", f"Crisis '{cid}': MULTI_ACTION needs >= 2 actions")
            for act in actions:
                if "rest" in act:
                    continue
                arch = act.get("target_arch")
                action = act.get("action")
                slot = act.get("slot")
                if arch and action and slot:
                    if not is_valid_command(arch, action, slot):
                        r.error("CAPABILITY",
                                f"Crisis '{cid}': {arch} {slot} can't do '{action}'")

        timeout = crisis.get("timeout_ms", 0)
        if timeout < 3000 or timeout > 15000:
            r.warn("CRISES",
                   f"Crisis '{cid}': timeout {timeout}ms unusual (expected 3000-15000)")

        penalty = crisis.get("penalty", "")
        if penalty not in CRISIS_PENALTIES:
            r.warn("CRISES", f"Crisis '{cid}': unknown penalty '{penalty}'")


def _check_phases(s, r):
    phases = s.get("phases", [])
    if not phases:
        r.error("PHASES", "No phases defined")
        return

    phase_ids = [p.get("id") for p in phases]

    # Intro check
    if phases[0].get("type") != "NARRATION" or phases[0].get("id") != "intro":
        r.error("PHASES", "First phase must be 'intro' with type NARRATION")

    # All required frantic phases
    for fid in FRANTIC_PHASE_IDS:
        if fid not in phase_ids:
            r.error("PHASES", f"Missing required frantic phase: {fid}")

    # All branch phases
    branch_ids = [p.get("id") for p in phases if p.get("type") == "BRANCH"]
    for bid in ("branch_1", "branch_2", "branch_3"):
        if bid not in branch_ids:
            r.error("PHASES", f"Missing required branch phase: {bid}")

    # Validate frantic phases
    crisis_ids = {c.get("id") for c in s.get("crises", [])}
    difficulty = s.get("meta", {}).get("difficulty", "medium")

    for phase in phases:
        ptype = phase.get("type")
        pid = phase.get("id", "???")

        if ptype == "FRANTIC":
            _check_frantic_phase(phase, pid, difficulty, crisis_ids, r)
        elif ptype == "PREFLIGHT":
            _check_preflight_phase(phase, pid, s, r)
        elif ptype == "BRANCH":
            threshold = phase.get("threshold")
            if threshold is not None and not (0 < threshold < 1):
                r.error("PHASES",
                        f"Branch '{pid}': threshold {threshold} should be in (0, 1)")


def _check_frantic_phase(phase, pid, difficulty, crisis_ids, r):
    """Validate a single FRANTIC phase."""
    diff_block = phase.get("difficulty")
    if diff_block is None:
        preset = PRESETS.get(difficulty, {}).get(pid)
        if preset is None:
            r.error("PHASES",
                    f"Phase '{pid}': no difficulty block and no preset "
                    f"for difficulty='{difficulty}'")
        return

    # Validate difficulty block fields
    cpm = diff_block.get("commands_per_min", {})
    start = cpm.get("start")
    end = cpm.get("end")
    if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
        r.error("PHASES", f"Phase '{pid}': commands_per_min needs numeric start and end")
    elif start > end:
        r.warn("PHASES", f"Phase '{pid}': commands_per_min.start > end (reverse ramp)")

    coop = diff_block.get("coop_ratio", 0)
    if not (0 <= coop <= 1):
        r.error("PHASES", f"Phase '{pid}': coop_ratio {coop} out of [0, 1]")

    open_ratio = diff_block.get("open_ratio", 0)
    if not (0 <= open_ratio <= 1):
        r.error("PHASES", f"Phase '{pid}': open_ratio {open_ratio} out of [0, 1]")

    # coop_ratio + open_ratio should not exceed 1.0
    if coop + open_ratio > 1.0:
        r.error("PHASES",
                f"Phase '{pid}': coop_ratio ({coop}) + open_ratio ({open_ratio}) "
                f"exceeds 1.0 — no room for direct commands")

    crisis = diff_block.get("crisis_chance_per_30s", 0)
    if not (0 <= crisis <= 1):
        r.error("PHASES", f"Phase '{pid}': crisis_chance_per_30s {crisis} out of [0, 1]")

    tm = diff_block.get("timeout_multiplier", 1)
    if tm < 0.5 or tm > 2.0:
        r.warn("PHASES", f"Phase '{pid}': timeout_multiplier {tm} seems extreme (0.5-2.0)")

    # Crisis references
    for cref in phase.get("crises", []):
        if cref not in crisis_ids:
            r.error("PHASES", f"Phase '{pid}': references unknown crisis '{cref}'")


def _check_preflight_phase(phase, pid, scenario, r):
    """Validate a PREFLIGHT phase — init commands for stateful controls."""
    init_commands = phase.get("init_commands")
    if init_commands is None:
        r.warn("PREFLIGHT", f"Phase '{pid}': PREFLIGHT has no init_commands")
        return

    if not isinstance(init_commands, dict):
        r.error("PREFLIGHT", f"Phase '{pid}': init_commands must be a dict keyed by archetype")
        return

    for arch, cmds in init_commands.items():
        if arch not in ARCHETYPES:
            r.error("PREFLIGHT",
                    f"Phase '{pid}': unknown archetype '{arch}' in init_commands")
            continue
        if not isinstance(cmds, list):
            r.error("PREFLIGHT",
                    f"Phase '{pid}': init_commands[{arch}] must be a list")
            continue
        for cmd in cmds:
            slot = cmd.get("slot")
            action = cmd.get("action")
            if slot and action:
                if not is_valid_command(arch, action, slot):
                    expected = CAPABILITY_MATRIX.get(arch, {}).get(slot, "NONE")
                    r.error("PREFLIGHT",
                            f"Phase '{pid}': {arch} {slot} expects "
                            f"'{expected}', got '{action}'")
                if action not in STATEFUL_ACTIONS:
                    r.warn("PREFLIGHT",
                           f"Phase '{pid}': {arch} {slot} action '{action}' "
                           f"is not stateful — pre-flight typically initializes "
                           f"stateful controls only")


def _check_outcomes(s, r):
    outcomes = s.get("outcomes")
    if not outcomes:
        r.error("OUTCOMES", "Missing 'outcomes' section")
        return

    for path in BRANCH_PATHS:
        if path not in outcomes:
            r.error("OUTCOMES", f"Missing outcome for path '{path}'")

    for path, ending in outcomes.items():
        if path not in BRANCH_PATHS:
            r.warn("OUTCOMES", f"Unexpected path key '{path}'")
            continue
        if not isinstance(ending, dict):
            r.error("OUTCOMES", f"Outcome '{path}' must be a dict")
            continue
        tier = ending.get("tier")
        if tier not in OUTCOME_TIERS:
            r.error("OUTCOMES", f"Outcome '{path}': unknown tier '{tier}'")
        for line in ending.get("narrator_lines", []):
            if len(line) > NARRATOR_LINE_MAX:
                r.error("OUTCOMES",
                        f"Outcome '{path}': narrator_line exceeds "
                        f"{NARRATOR_LINE_MAX} chars")


def _check_narrator(s, r):
    narrator = s.get("narrator")
    if not narrator:
        r.warn("NARRATOR", "Missing 'narrator' section")
        return
    if "voice" not in narrator:
        r.warn("NARRATOR", "Missing narrator.voice")
    for line in narrator.get("between_commands_lines", []):
        if len(line) > NARRATOR_LINE_MAX:
            r.error("NARRATOR",
                    f"Ambient line exceeds {NARRATOR_LINE_MAX} chars: "
                    f"'{line[:50]}...'")


# ─── Internal Helpers ────────────────────────────────────────────────

def _check_label_lengths(cmd, cid, pool_name, r):
    """Check label and narrator_line lengths on a command."""
    label = cmd.get("label", "")
    if len(label) > SCREEN_LABEL_MAX:
        r.error("LABEL", f"{pool_name} cmd '{cid}': label exceeds {SCREEN_LABEL_MAX} chars")
    nar = cmd.get("narrator_line", "")
    if len(nar) > NARRATOR_LINE_MAX:
        r.error("LABEL", f"{pool_name} cmd '{cid}': narrator_line exceeds {NARRATOR_LINE_MAX} chars")
