#!/usr/bin/env python3
"""Structural checker for Tundra models (YAML in .tundra files)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "tundra.schema.json"

VAGUE_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"\btoo high\b",
        r"\btoo low\b",
        r"\breasonable\b",
        r"\bsufficient\b",
        r"\bsuitable\b",
        r"\bappropriate\b",
        r"\bsoon\b",
        r"\blow risk\b",
        r"\bhigh risk\b",
        r"\bhigh relative to\b",
        r"\blow relative to\b",
        r"\bfalls? between\b",
        r"\bfall between\b",
    ]
]

STEP_PREFIX = re.compile(r"^(Given|When|Then|And)\b")


def load_deps():
    try:
        import yaml  # type: ignore
    except ImportError:
        print(
            "Missing dependency: PyYAML. Install with:\n"
            "  pip install -r requirements-dev.txt",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        import jsonschema  # type: ignore
    except ImportError:
        print(
            "Missing dependency: jsonschema. Install with:\n"
            "  pip install -r requirements-dev.txt",
            file=sys.stderr,
        )
        sys.exit(2)
    return yaml, jsonschema


def find_models() -> list[Path]:
    paths: list[Path] = []
    paths.extend(sorted((ROOT / "examples").rglob("*.tundra")))
    skill_ex = ROOT / ".grok" / "skills" / "tundra" / "references" / "example.tundra"
    if skill_ex.is_file():
        paths.append(skill_ex)
    return paths


def check_file(path: Path, schema: dict, yaml, jsonschema) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        return [f"YAML parse error: {exc}"], warnings

    if data is None:
        return ["empty document"], warnings
    if not isinstance(data, dict):
        return ["root must be a mapping"], warnings

    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = ".".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema [{loc}]: {err.message}")

    if errors:
        return errors, warnings

    roles = set(data.get("roles") or [])
    for i, proc in enumerate(data.get("processes") or []):
        actor = proc.get("actor")
        if actor and actor != "System" and actor not in roles:
            errors.append(
                f"process[{i}] ({proc.get('name')!r}): actor {actor!r} "
                f"is not in roles and is not 'System'"
            )

    for i, scen in enumerate(data.get("scenarios") or []):
        for j, step in enumerate(scen.get("steps") or []):
            if not STEP_PREFIX.match(step.strip()):
                warnings.append(
                    f"scenario[{i}] step[{j}]: does not start with "
                    f"Given/When/Then/And: {step!r}"
                )

    for i, contract in enumerate(data.get("contracts") or []):
        for pat in VAGUE_PATTERNS:
            if pat.search(contract):
                warnings.append(
                    f"contract[{i}]: possibly vague phrasing ({pat.pattern}): {contract!r}"
                )
                break

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    yaml, jsonschema = load_deps()
    parser = argparse.ArgumentParser(description="Check Tundra .tundra YAML models")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Model files (default: --all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all models under examples/ and skill example",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Exit non-zero if any warnings (e.g. vague contracts)",
    )
    args = parser.parse_args(argv)

    if not SCHEMA_PATH.is_file():
        print(f"Schema not found: {SCHEMA_PATH}", file=sys.stderr)
        return 2

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    if args.all or not args.paths:
        paths = find_models()
    else:
        paths = []
        for p in args.paths:
            if p.is_dir():
                paths.extend(sorted(p.rglob("*.tundra")))
            else:
                paths.append(p)

    if not paths:
        print("No .tundra files to check", file=sys.stderr)
        return 2

    any_error = False
    any_warning = False
    for path in paths:
        rel = path if path.is_absolute() else path
        try:
            display = path.resolve().relative_to(ROOT)
        except ValueError:
            display = path
        errors, warnings = check_file(path, schema, yaml, jsonschema)
        if not errors and not warnings:
            print(f"OK  {display}")
            continue
        if errors:
            any_error = True
            print(f"FAIL {display}")
            for e in errors:
                print(f"  error: {e}")
        else:
            print(f"OK  {display} (with warnings)")
        for w in warnings:
            any_warning = True
            print(f"  warning: {w}")

    if any_error:
        return 1
    if args.strict_warnings and any_warning:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
