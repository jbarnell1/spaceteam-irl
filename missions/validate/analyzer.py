"""Difficulty and content analyzer for Spaceteam IRL scenarios.

Produces a human-readable report covering command distribution,
cooperative network, crisis overview, difficulty curves per phase,
path timing estimates, and a side-by-side difficulty preset comparison.
"""

from .capability_matrix import (
    ARCHETYPES, FRANTIC_PHASE_IDS, PATH_PHASES, ELEMENT_ARCHETYPES, get_tier,
)
from .difficulty_presets import (
    PRESETS, DIFFICULTY_LEVELS, resolve_phase_difficulty, estimate_total_commands,
)


def analyze(scenario):
    """Return a full human-readable analysis report string."""
    sections = [
        _header(scenario),
        _command_distribution(scenario),
        _open_command_summary(scenario),
        _coop_network(scenario),
        _crisis_overview(scenario),
        _phase_difficulty_curves(scenario),
        _path_timing(scenario),
        _estimated_command_totals(scenario),
        _difficulty_comparison(scenario),
    ]
    return "\n".join(sections)


# ─── Report Sections ─────────────────────────────────────────────────

def _header(s):
    meta = s.get("meta", {})
    pc = meta.get("player_count", {})
    dur = meta.get("duration_sec", {})
    return "\n".join([
        "=" * 60,
        f"SCENARIO ANALYSIS: {meta.get('title', '???')}",
        f"Pack: {meta.get('pack', '???')}  |  Difficulty: {meta.get('difficulty', '???')}",
        f"Players: {pc.get('min', '?')}-{pc.get('max', '?')}",
        f"Duration: {dur.get('min', '?')}-{dur.get('max', '?')}s",
        "=" * 60,
    ])


def _command_distribution(s):
    pools = s.get("command_pools", {})
    direct = pools.get("direct", [])
    coop = pools.get("cooperative", [])
    open_cmds = pools.get("open", [])

    lines = ["\n--- Command Distribution ---"]
    lines.append(f"Total: {len(direct)} direct + {len(coop)} cooperative "
                 f"+ {len(open_cmds)} open "
                 f"= {len(direct) + len(coop) + len(open_cmds)} commands\n")

    header = (f"{'Archetype':<12} {'Direct':>6} "
              f"{'T1':>4} {'T2':>4} {'T3':>4} "
              f"{'Coop(exec)':>10} {'Coop(shout)':>11}")
    lines.append(header)
    lines.append("-" * len(header))

    for arch in ARCHETYPES:
        arch_direct = [c for c in direct if c.get("target_arch") == arch]
        t1 = sum(1 for c in arch_direct if c.get("tier") == "T1")
        t2 = sum(1 for c in arch_direct if c.get("tier") == "T2")
        t3 = sum(1 for c in arch_direct if c.get("tier") == "T3")
        coop_exec = sum(1 for c in coop if c.get("target_arch") == arch)
        coop_shout = sum(1 for c in coop if c.get("display_on") == arch)
        lines.append(f"{arch:<12} {len(arch_direct):>6} "
                     f"{t1:>4} {t2:>4} {t3:>4} "
                     f"{coop_exec:>10} {coop_shout:>11}")

    t1_tot = sum(1 for c in direct if c.get("tier") == "T1")
    t2_tot = sum(1 for c in direct if c.get("tier") == "T2")
    t3_tot = sum(1 for c in direct if c.get("tier") == "T3")
    lines.append("-" * len(header))
    lines.append(f"{'TOTAL':<12} {len(direct):>6} "
                 f"{t1_tot:>4} {t2_tot:>4} {t3_tot:>4} "
                 f"{len(coop):>10} {len(coop):>11}")

    total = len(direct)
    if total > 0:
        lines.append(f"\nTier mix: T1={t1_tot/total:.0%}  "
                     f"T2={t2_tot/total:.0%}  T3={t3_tot/total:.0%}")
    return "\n".join(lines)


def _open_command_summary(s):
    open_cmds = s.get("command_pools", {}).get("open", [])
    if not open_cmds:
        return "\n--- Open Commands ---\n(none)"

    lines = ["\n--- Open Commands ---", f"Total: {len(open_cmds)}\n"]

    # Group by action type
    by_action = {}
    for cmd in open_cmds:
        action = cmd.get("action", "???")
        by_action.setdefault(action, []).append(cmd)

    for action, cmds in sorted(by_action.items()):
        archetypes = ELEMENT_ARCHETYPES.get(action, [])
        tier = get_tier(action) or "?"
        lines.append(f"  {action} ({tier}) — responders: {', '.join(archetypes)}")
        for cmd in cmds:
            lines.append(f"    {cmd.get('id', '???')}: {cmd.get('label', '???')}")

    return "\n".join(lines)


def _coop_network(s):
    coop = s.get("command_pools", {}).get("cooperative", [])
    lines = ["\n--- Cooperative Network ---"]

    pairs = {}
    for cmd in coop:
        pair = (cmd.get("display_on", "?"), cmd.get("target_arch", "?"))
        pairs.setdefault(pair, []).append(cmd.get("id"))

    lines.append(f"Unique shouter->executor pairs: {len(pairs)}\n")
    row_fmt = f"{'Shouter':<12} -> {'Executor':<12} {'#':>2}  Commands"
    lines.append(row_fmt)
    lines.append("-" * 60)
    for (shouter, executor), cmds in sorted(pairs.items()):
        lines.append(f"{shouter:<12} -> {executor:<12} {len(cmds):>2}  "
                     f"{', '.join(cmds)}")
    return "\n".join(lines)


def _crisis_overview(s):
    crises = s.get("crises", [])
    lines = ["\n--- Crisis Events ---", f"Total: {len(crises)}\n"]
    for crisis in crises:
        cid = crisis.get("id", "???")
        ctype = crisis.get("type", "???")
        timeout = crisis.get("timeout_ms", 0)
        penalty = crisis.get("penalty", "???")
        lines.append(f"  {cid}: {ctype} | timeout={timeout}ms | penalty={penalty}")
    return "\n".join(lines)


def _phase_difficulty_curves(s):
    lines = ["\n--- Phase Difficulty Curves ---"]
    header = (f"{'Phase':<16} {'Dur':>4} {'Cmd/min':>10} "
              f"{'Coop%':>6} {'Open%':>6} {'Crisis%':>8} {'Timeout*':>9} {'#Crises':>8}")
    lines.append(header)
    lines.append("-" * len(header))

    for phase in s.get("phases", []):
        if phase.get("type") != "FRANTIC":
            continue
        pid = phase.get("id", "???")
        dur = phase.get("duration_sec", "?")

        diff = resolve_phase_difficulty(s, phase)
        if diff is None:
            lines.append(f"{pid:<16} {dur:>4}  (no difficulty data)")
            continue

        if not isinstance(dur, int):
            dur = diff.get("duration_sec", "?")

        cpm = diff.get("commands_per_min", {})
        cpm_str = f"{cpm.get('start', '?')}->{cpm.get('end', '?')}"
        coop = diff.get("coop_ratio", 0)
        open_r = diff.get("open_ratio", 0)
        crisis = diff.get("crisis_chance_per_30s", 0)
        tm = diff.get("timeout_multiplier", 1)
        n_crises = len(phase.get("crises", []))

        lines.append(f"{pid:<16} {dur:>4} {cpm_str:>10} "
                     f"{coop:>5.0%} {open_r:>5.0%} {crisis:>7.0%} "
                     f"{tm:>9.2f} {n_crises:>8}")
    return "\n".join(lines)


def _path_timing(s):
    lines = ["\n--- Path Timing (estimated) ---"]
    phases = {p["id"]: p for p in s.get("phases", []) if "id" in p}
    difficulty = s.get("meta", {}).get("difficulty", "medium")
    intro_dur = phases.get("intro", {}).get("duration_sec", 60)
    branch_narration_sec = 15  # ~15s per branch transition

    for path_name, phase_ids in PATH_PHASES.items():
        total = intro_dur
        for pid in phase_ids:
            phase = phases.get(pid, {})
            dur = phase.get("duration_sec")
            if dur is None:
                preset = PRESETS.get(difficulty, {}).get(pid, {})
                dur = preset.get("duration_sec", 0)
            total += dur
            total += branch_narration_sec
        mins = total / 60
        lines.append(f"  {path_name}: ~{total}s ({mins:.1f} min)")
    return "\n".join(lines)


def _estimated_command_totals(s):
    lines = ["\n--- Estimated Command Totals Per Path ---"]
    difficulty = s.get("meta", {}).get("difficulty", "medium")

    for path_name, phase_ids in PATH_PHASES.items():
        total = 0
        parts = []
        for pid in phase_ids:
            est = estimate_total_commands(difficulty, pid)
            total += est
            parts.append(f"{pid}={est}")
        lines.append(f"  {path_name}: ~{total} commands  ({', '.join(parts)})")
    return "\n".join(lines)


def _difficulty_comparison(s):
    lines = ["\n--- Difficulty Preset Comparison ---"]
    lines.append("What each difficulty level would feel like for this scenario's phases.\n")

    for level in DIFFICULTY_LEVELS:
        preset = PRESETS.get(level, {})
        lines.append(f"  [{level.upper()}]")
        for pid in FRANTIC_PHASE_IDS:
            params = preset.get(pid)
            if params is None:
                continue
            cpm = params.get("commands_per_min", {})
            lines.append(
                f"    {pid:<16} {params.get('duration_sec', '?'):>4}s "
                f"{cpm.get('start', '?')}->{cpm.get('end', '?')} cmd/min  "
                f"coop={params.get('coop_ratio', 0):.0%}  "
                f"open={params.get('open_ratio', 0):.0%}  "
                f"crisis={params.get('crisis_chance_per_30s', 0):.0%}  "
                f"timeout*{params.get('timeout_multiplier', 1):.2f}"
            )
        lines.append("")
    return "\n".join(lines)
