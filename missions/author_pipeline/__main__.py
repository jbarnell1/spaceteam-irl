"""CLI for the Spaceteam IRL author pipeline.

Usage:
    uv run python -m missions.author_pipeline compile   <src.json>  [-o <out.json>]
    uv run python -m missions.author_pipeline decompile <mat.json>  [-o <out.src.json>]
    uv run python -m missions.author_pipeline roundtrip <mat.json> [<mat2.json> ...]
"""

import argparse
import json
import sys
from pathlib import Path

from .compiler import compile_scenario
from .decompiler import decompile_scenario


# ──────────────────────────────────────────────────────────────────────
# Round-trip comparison
# ──────────────────────────────────────────────────────────────────────

def _normalize(obj):
    """Recursively sort dict keys and normalize types for comparison."""
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_normalize(v) for v in obj]
    return obj


def _deep_diff(path, a, b, diffs):
    """Collect human-readable differences between two JSON-like structures."""
    if isinstance(a, dict) and isinstance(b, dict):
        all_keys = set(a) | set(b)
        for k in sorted(all_keys):
            p = f"{path}.{k}"
            if k not in a:
                diffs.append(f"  MISSING in recompiled: {p}")
            elif k not in b:
                diffs.append(f"  EXTRA in recompiled:   {p}")
            else:
                _deep_diff(p, a[k], b[k], diffs)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f"  LENGTH MISMATCH at {path}: {len(a)} vs {len(b)}")
        for i in range(min(len(a), len(b))):
            _deep_diff(f"{path}[{i}]", a[i], b[i], diffs)
    else:
        if a != b:
            # Distinguish bool vs int (JSON true ≠ 1)
            if isinstance(a, bool) or isinstance(b, bool):
                if type(a) is not type(b) or a != b:
                    diffs.append(f"  VALUE DIFF at {path}: {a!r} vs {b!r}")
            else:
                diffs.append(f"  VALUE DIFF at {path}: {a!r} vs {b!r}")


def roundtrip_check(materialized):
    """Decompile then recompile; return (success, diffs_list)."""
    source = decompile_scenario(materialized)
    recompiled = compile_scenario(source)

    norm_orig = _normalize(materialized)
    norm_re = _normalize(recompiled)

    if norm_orig == norm_re:
        return True, []

    diffs = []
    _deep_diff("$", materialized, recompiled, diffs)
    return False, diffs


# ──────────────────────────────────────────────────────────────────────
# CLI commands
# ──────────────────────────────────────────────────────────────────────

def cmd_compile(args):
    src = json.loads(Path(args.input).read_text(encoding="utf-8"))
    materialized = compile_scenario(src)
    text = json.dumps(materialized, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Compiled → {args.output}")
    else:
        sys.stdout.write(text)


def cmd_decompile(args):
    mat = json.loads(Path(args.input).read_text(encoding="utf-8"))
    source = decompile_scenario(mat)
    text = json.dumps(source, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Decompiled → {args.output}")
    else:
        sys.stdout.write(text)


def cmd_roundtrip(args):
    all_pass = True
    for path in args.inputs:
        name = Path(path).name
        mat = json.loads(Path(path).read_text(encoding="utf-8"))
        ok, diffs = roundtrip_check(mat)
        if ok:
            print(f"  PASS  {name}")
        else:
            print(f"  FAIL  {name}")
            for d in diffs[:20]:
                print(d)
            if len(diffs) > 20:
                print(f"  ... and {len(diffs) - 20} more diffs")
            all_pass = False
    if not all_pass:
        sys.exit(1)
    print(f"\nAll {len(args.inputs)} scenario(s) round-trip clean.")


# ──────────────────────────────────────────────────────────────────────
# Argument parser
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="missions.author_pipeline",
        description="Spaceteam IRL scenario author pipeline",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # compile
    p_compile = sub.add_parser("compile", help="Compile source → materialized JSON")
    p_compile.add_argument("input", help="Path to source .src.json")
    p_compile.add_argument("-o", "--output", help="Output path (default: stdout)")

    # decompile
    p_decompile = sub.add_parser("decompile", help="Decompile materialized → source JSON")
    p_decompile.add_argument("input", help="Path to materialized .json")
    p_decompile.add_argument("-o", "--output", help="Output path (default: stdout)")

    # roundtrip
    p_roundtrip = sub.add_parser("roundtrip", help="Validate round-trip on materialized scenario(s)")
    p_roundtrip.add_argument("inputs", nargs="+", help="One or more materialized .json files")

    args = parser.parse_args()
    {"compile": cmd_compile, "decompile": cmd_decompile, "roundtrip": cmd_roundtrip}[args.command](args)


if __name__ == "__main__":
    main()
