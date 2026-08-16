#!/usr/bin/env python3
"""Checker for Tundra models (YAML in .tundra files).

Enforces schema plus semantic links the format depends on:
contract quotes, requires/results vs states, subject-named states,
regulatory provenance (via cite_resolve), etc.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "tundra.schema.json"
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from cite_resolve import (  # noqa: E402
    check_provenance,
    cites_from_models,
    enumerate_source_coverage,
    split_paragraph_point,
)
from model_checks import (  # noqa: E402
    check_contract_demonstration,
    check_enforced_by_usage,
    check_expires_handlers,
    check_lifecycle_reachability,
    check_processes,
    check_role_usage,
    check_scenarios,
    check_state_subjects,
    check_system_not_a_role,
    check_vagueness,
    classify_model_kind,
    collect_states,
    index_contracts,
)


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
    """Discover models for --all (active corpus only; not archive/)."""
    paths: list[Path] = []
    for sub in ("models", "examples"):
        d = ROOT / sub
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*.tundra")):
            if "archive" in p.parts:
                continue
            if "bad-structure" in p.parts or "bad-contracts" in p.parts:
                continue
            if "_fixtures" in p.parts:
                continue
            paths.append(p)
    skill_refs = ROOT / ".grok" / "skills" / "tundra" / "references"
    for name in ("example.tundra", "example-regulation.tundra"):
        skill_ex = skill_refs / name
        if skill_ex.is_file():
            paths.append(skill_ex)
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


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

    # --- Semantic checks (only after schema OK) ---
    roles = [r for r in (data.get("roles") or []) if isinstance(r, str)]
    role_set = set(roles)
    errors.extend(check_system_not_a_role(roles))

    state_names, state_objects = collect_states(data)
    state_set = set(state_names)
    errors.extend(check_state_subjects(state_names))

    cidx = index_contracts(data)
    errors.extend(cidx.errors)

    processes = [p for p in (data.get("processes") or []) if isinstance(p, dict)]
    is_obligations, is_lifecycle, kind_errs = classify_model_kind(
        data, processes, state_names
    )
    errors.extend(kind_errs)

    pscan = check_processes(processes, role_set, state_set, cidx.id_set)
    errors.extend(pscan.errors)

    sscan = check_scenarios(data, cidx.text_set, cidx.id_set)
    errors.extend(sscan.errors)
    warnings.extend(sscan.warnings)

    warnings.extend(
        check_contract_demonstration(
            data, sscan.quoted_texts, sscan.quoted_ids, pscan.enforced_refs
        )
    )
    warnings.extend(
        check_enforced_by_usage(cidx.ids, pscan.enforced_refs, bool(processes))
    )

    if is_lifecycle and processes:
        le, lw = check_lifecycle_reachability(
            processes,
            state_names,
            state_objects,
            state_set,
            pscan.results_produced,
            pscan.requires_consumed,
        )
        errors.extend(le)
        warnings.extend(lw)

    warnings.extend(
        check_role_usage(roles, pscan.actors_used, cidx.texts, is_lifecycle)
    )

    expires_states: list[str] = [
        name
        for entry in state_objects
        if isinstance((name := entry.get("name")), str) and "expires_in" in entry
    ]
    warnings.extend(check_expires_handlers(processes, expires_states))
    warnings.extend(check_vagueness(data, roles, state_names))

    pe, pw = check_provenance(data, path, ROOT)
    errors.extend(pe)
    warnings.extend(pw)

    return errors, warnings


def run_coverage(target: Path, yaml) -> int:
    """Print instrument coverage for a regulations sample directory."""
    if target.is_file():
        model_paths = [target]
        sources_dir = target.parent / "sources"
    else:
        model_paths = sorted(
            p for p in target.rglob("*.tundra") if "_fixtures" not in p.parts
        )
        sources_dir = target / "sources"
        if not sources_dir.is_dir():
            for p in model_paths:
                cand = p.parent / "sources"
                if cand.is_dir():
                    sources_dir = cand
                    break

    if not sources_dir.is_dir():
        print(f"No sources/ under {target}", file=sys.stderr)
        return 2

    inventory = enumerate_source_coverage(sources_dir)
    cited = cites_from_models(model_paths, yaml)

    cited_paras: dict[str, set[str]] = {a: set() for a in inventory}
    cited_points: dict[str, set[str]] = {a: set() for a in inventory}
    for c in cited:
        art = re.sub(r"[^\d]", "", c["article"]) or c["article"]
        if art.isdigit():
            art = str(int(art))
        pnum, point = split_paragraph_point(c.get("paragraph") or "")
        if pnum and pnum.isdigit():
            cited_paras.setdefault(art, set()).add(pnum)
        if point:
            cited_points.setdefault(art, set()).add(point)
        elif art and not pnum:
            cited_paras.setdefault(art, set())

    total_p = total_pc = total_pts = total_ptc = 0
    print(f"Coverage for {sources_dir} ({len(model_paths)} model file(s))\n")
    for art in sorted(inventory.keys(), key=lambda x: int(x) if x.isdigit() else x):
        inv = inventory[art]
        paras = inv["paragraphs"]
        points = inv["points"]
        cp = cited_paras.get(art, set())
        missing_p = sorted(paras - cp, key=lambda x: int(x) if x.isdigit() else 0)
        have_p = sorted(paras & cp, key=lambda x: int(x) if x.isdigit() else 0)
        cpt = cited_points.get(art, set())
        missing_pt = sorted(points - cpt)
        have_pt = sorted(points & cpt)
        total_p += len(paras)
        total_pc += len(paras & cp)
        total_pts += len(points)
        total_ptc += len(points & cpt)
        print(f"Article {art} ({inv['file']}):")
        print(
            f"  paragraphs: cited {', '.join(have_p) or '—'}; "
            f"missing {', '.join(missing_p) or '—'}"
        )
        if points:
            print(
                f"  points:     cited {', '.join(have_pt) or '—'}; "
                f"missing {', '.join(missing_pt) or '—'}"
            )
        print()
    print(
        f"Summary: {total_pc}/{total_p} paragraphs, "
        f"{total_ptc}/{total_pts} points cited "
        f"(partial coverage is normal for thin slices)"
    )
    return 0


def print_report(display: object, errors: list[str], warnings: list[str]) -> None:
    if not errors and not warnings:
        print(f"OK  {display}")
        return
    if errors:
        print(f"FAIL {display}")
    else:
        print(f"OK  {display} (with warnings)")
    for e in errors:
        print(f"  error: {e}")
    for w in warnings:
        print(f"  warning: {w}")


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
        help="Check models/, examples/, and skill example",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Exit non-zero if any warnings",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Report article/paragraph/point coverage vs sources/ (needs a path)",
    )
    args = parser.parse_args(argv)

    if args.coverage:
        if not args.paths:
            print(
                "usage: check_tundra.py --coverage <regulations-dir-or-model>",
                file=sys.stderr,
            )
            return 2
        return run_coverage(args.paths[0], yaml)

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
                paths.extend(
                    sorted(
                        x
                        for x in p.rglob("*.tundra")
                        if "_fixtures" not in x.parts or p.name == "_fixtures"
                    )
                )
            else:
                paths.append(p)

    if not paths:
        print("No .tundra files to check", file=sys.stderr)
        return 2

    any_error = False
    any_warning = False
    for path in paths:
        try:
            display = path.resolve().relative_to(ROOT)
        except ValueError:
            display = path
        errors, warnings = check_file(path, schema, yaml, jsonschema)
        print_report(display, errors, warnings)
        if errors:
            any_error = True
        if warnings:
            any_warning = True

    if any_error:
        return 1
    if args.strict_warnings and any_warning:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
