"""CLI entry point for Spaceteam IRL scenario validation and analysis.

Usage:
    python -m missions.validate <scenario.json> [--analyze] [--difficulty LEVEL]

Run from the repository root (c:\\spaceteam_irl).
"""

import argparse
import copy
import json
import sys
from pathlib import Path

from .validator import validate
from .analyzer import analyze
from .difficulty_presets import (
    DIFFICULTY_LEVELS, PRESETS, BRANCH_THRESHOLDS, INTRO_DURATION,
)


def main():
    parser = argparse.ArgumentParser(
        prog="python -m missions.validate",
        description="Validate and analyze Spaceteam IRL scenario JSON files.",
    )
    parser.add_argument("scenario", help="Path to scenario JSON file")
    parser.add_argument(
        "--analyze", "-a", action="store_true",
        help="Print detailed difficulty and content analysis",
    )
    parser.add_argument(
        "--difficulty", "-d", choices=DIFFICULTY_LEVELS,
        help="Override difficulty level for analysis",
    )
    parser.add_argument(
        "--resolve", "-r", action="store_true",
        help="Print resolved JSON with preset difficulty filled in",
    )
    args = parser.parse_args()

    path = Path(args.scenario)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    if args.difficulty:
        scenario.setdefault("meta", {})["difficulty"] = args.difficulty

    # Always validate
    result = validate(scenario)
    print(result.summary())

    # Optionally analyze
    if args.analyze:
        print()
        print(analyze(scenario))

    # Optionally resolve presets into JSON
    if args.resolve:
        resolved = _resolve_presets(scenario)
        print("\n--- Resolved JSON ---")
        print(json.dumps(resolved, indent=2))

    sys.exit(0 if result.passed else 1)


def _resolve_presets(scenario):
    """Return a deep copy with preset-based difficulty parameters filled in."""
    s = copy.deepcopy(scenario)
    difficulty = s.get("meta", {}).get("difficulty", "medium")
    preset = PRESETS.get(difficulty, {})

    for phase in s.get("phases", []):
        if phase.get("type") != "FRANTIC":
            continue
        pid = phase.get("id")
        if "difficulty" not in phase or not isinstance(phase.get("difficulty"), dict):
            params = preset.get(pid)
            if params:
                phase_params = dict(params)
                dur = phase_params.pop("duration_sec", None)
                phase["difficulty"] = phase_params
                if dur and "duration_sec" not in phase:
                    phase["duration_sec"] = dur

    # Fill branch thresholds
    threshold = BRANCH_THRESHOLDS.get(difficulty, 0.55)
    for phase in s.get("phases", []):
        if phase.get("type") == "BRANCH":
            if "threshold" not in phase:
                phase["threshold"] = threshold

    # Fill intro duration
    intro_dur = INTRO_DURATION.get(difficulty, 60)
    for phase in s.get("phases", []):
        if phase.get("id") == "intro" and "duration_sec" not in phase:
            phase["duration_sec"] = intro_dur

    return s


if __name__ == "__main__":
    main()
