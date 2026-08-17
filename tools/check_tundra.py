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
    parse_out_of_scope,
    resolve_quote_subparagraph,
    split_paragraph_point,
    units_excluded_by_out_of_scope,
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
    check_implement_as_hints,
    check_vagueness,
    classify_model_kind,
    collect_states,
    demonstrated_contract_keys,
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


def _coerce_yaml_dates(obj):
    """YAML unquoted dates become datetime.date; schema expects strings."""
    import datetime as _dt

    if isinstance(obj, dict):
        return {k: _coerce_yaml_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_coerce_yaml_dates(v) for v in obj]
    if isinstance(obj, _dt.datetime):
        return obj.date().isoformat()
    if isinstance(obj, _dt.date):
        return obj.isoformat()
    return obj


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

    data = _coerce_yaml_dates(data)

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
        check_enforced_by_usage(
            cidx.ids, pscan.enforced_refs, bool(processes), data=data
        )
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
        check_role_usage(
            roles,
            pscan.actors_used,
            cidx.texts,
            is_lifecycle,
            regulatory=isinstance(data.get("regulation"), dict),
        )
    )

    expires_states: list[str] = [
        name
        for entry in state_objects
        if isinstance((name := entry.get("name")), str) and "expires_in" in entry
    ]
    warnings.extend(check_expires_handlers(processes, expires_states))
    warnings.extend(check_vagueness(data, roles, state_names))
    warnings.extend(check_implement_as_hints(data))
    _ids, _texts, dem_w = demonstrated_contract_keys(data)
    warnings.extend(dem_w)

    pe, pw = check_provenance(data, path, ROOT)
    errors.extend(pe)
    warnings.extend(pw)

    return errors, warnings


def run_coverage(target: Path, yaml) -> int:
    """Print instrument coverage (quoted cites only) vs sources/ inventory."""
    from cite_resolve import (  # local reuse
        load_article_excerpt,
        parse_nested_point_spans,
        parse_paragraph_spans,
    )

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

    # Per-model implementable-by-design contracts + out_of_scope unions
    dem_by_model: dict[str, tuple[set[str], set[str]]] = {}
    dem_extra_warnings: list[str] = []
    oos_all: set[tuple[str, str]] = set()
    for mp in model_paths:
        try:
            data = yaml.safe_load(mp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if isinstance(data, dict):
            ids, texts, dw = demonstrated_contract_keys(data)
            dem_by_model[str(mp)] = (ids, texts)
            dem_extra_warnings.extend(dw)
            reg = data.get("regulation")
            if isinstance(reg, dict):
                oos_all |= parse_out_of_scope(reg)

    quoted = [c for c in cited if (c.get("quote") or "").strip()]
    bare = [c for c in cited if not (c.get("quote") or "").strip()]

    cited_units: dict[str, set[str]] = {a: set() for a in inventory}
    impl_units: dict[str, set[str]] = {a: set() for a in inventory}
    cited_points_valid: dict[str, set[str]] = {a: set() for a in inventory}
    impl_points_valid: dict[str, set[str]] = {a: set() for a in inventory}

    excerpt_cache: dict[str, str] = {}
    for c in quoted:
        art = re.sub(r"[^\d]", "", c["article"]) or c["article"]
        if art.isdigit():
            art = str(int(art))
        pnum, point = split_paragraph_point(c.get("paragraph") or "")
        dem_ids, dem_texts = dem_by_model.get(c.get("model", ""), (set(), set()))
        is_impl = False
        cid = c.get("contract_id") or ""
        ctext = c.get("contract_text") or ""
        if cid and cid in dem_ids:
            is_impl = True
        if ctext and ctext in dem_texts:
            is_impl = True

        if pnum and pnum.isdigit():
            if art not in excerpt_cache:
                _p, text = load_article_excerpt(sources_dir, art)
                excerpt_cache[art] = text or ""
            spans = parse_paragraph_spans(excerpt_cache.get(art, ""))
            body = spans.get(pnum, "")
            # Multi-duty honesty: credit subparagraph unit, not whole paragraph
            sub_ord = resolve_quote_subparagraph(body, c.get("quote") or "")
            if sub_ord:
                unit = f"{pnum}¶{sub_ord}"
            else:
                unit = pnum
            cited_units.setdefault(art, set()).add(unit)
            if is_impl:
                impl_units.setdefault(art, set()).add(unit)
            if point and pnum in spans and point in parse_nested_point_spans(
                spans[pnum]
            ):
                cited_points_valid.setdefault(art, set()).add(point)
                if is_impl:
                    impl_points_valid.setdefault(art, set()).add(point)

    total_u = total_uc = total_ui = total_pts = total_ptc = total_pti = 0
    total_oos = 0
    print(f"Coverage for {sources_dir} ({len(model_paths)} model file(s))\n")
    print(
        f"Cites: {len(quoted)} quoted / {len(bare)} bare "
        f"(only quoted cites count toward coverage)\n"
    )
    if oos_all:
        oos_fmt = ", ".join(
            f"{a}:{p}" for a, p in sorted(oos_all, key=lambda t: (t[0], t[1]))
        )
        print(f"out_of_scope (excluded from denominator): {oos_fmt}\n")

    for art in sorted(inventory.keys(), key=lambda x: int(x) if x.isdigit() else x):
        inv = inventory[art]
        units = set(inv.get("units") or inv["paragraphs"])
        drop = units_excluded_by_out_of_scope(units, oos_all, art)
        denom = units - drop
        total_oos += len(drop)
        points = inv["points"]
        cu = cited_units.get(art, set()) & denom
        iu = impl_units.get(art, set()) & denom
        # also allow bare paragraph credit to count a multi-unit only if all hit — no:
        # cited may have '6¶2'; denom has '6¶1','6¶2',...
        missing_u = sorted(
            denom - cu,
            key=lambda x: (
                int(x.split("¶")[0]) if x.split("¶")[0].isdigit() else 0,
                x,
            ),
        )
        have_u = sorted(
            denom & cu,
            key=lambda x: (
                int(x.split("¶")[0]) if x.split("¶")[0].isdigit() else 0,
                x,
            ),
        )
        have_i = sorted(
            denom & iu,
            key=lambda x: (
                int(x.split("¶")[0]) if x.split("¶")[0].isdigit() else 0,
                x,
            ),
        )
        cpt = cited_points_valid.get(art, set())
        ipt = impl_points_valid.get(art, set())
        missing_pt = sorted(points - cpt)
        have_pt = sorted(points & cpt)
        have_ipt = sorted(points & ipt)
        total_u += len(denom)
        total_uc += len(denom & cu)
        total_ui += len(denom & iu)
        total_pts += len(points)
        total_ptc += len(points & cpt)
        total_pti += len(points & ipt)
        print(f"Article {art} ({inv['file']}):")
        print(
            f"  units:  quoted {', '.join(have_u) or '—'}; "
            f"implementable {', '.join(have_i) or '—'}; "
            f"missing {', '.join(missing_u) or '—'}"
        )
        if drop:
            print(f"  out_of_scope units: {', '.join(sorted(drop))}")
        if points:
            print(
                f"  points: quoted {', '.join(have_pt) or '—'}; "
                f"implementable {', '.join(have_ipt) or '—'}; "
                f"missing {', '.join(missing_pt) or '—'}"
            )
        print()
    print(
        f"Quoted coverage:         {total_uc}/{total_u} duty-units, "
        f"{total_ptc}/{total_pts} points"
    )
    print(
        f"Implementable (by design): {total_ui}/{total_u} duty-units, "
        f"{total_pti}/{total_pts} points "
        f"(failure Scenario 'is broken' AND evidence|enforced_by|implemented_at — "
        f"design intent, not assurance)"
    )
    oos_note = f"; {total_oos} unit(s) out_of_scope" if total_oos else ""
    print(
        f"(duty-units = paragraphs, split into ¶N when multi-subparagraph; "
        f"from sources/, not as published{oos_note})"
    )
    for w in dem_extra_warnings:
        # rename noise in warnings for display
        print(f"  note: {w.replace('demonstrated coverage', 'implementable (by design)')}")

    # Surface checker warnings so coverage never travels alone (review 5/6)
    if SCHEMA_PATH.is_file():
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        import jsonschema as _js
        from collections import Counter

        warn_n = err_n = 0
        cats: Counter[str] = Counter()
        for mp in model_paths:
            errs, warns = check_file(mp, schema, yaml, _js)
            err_n += len(errs)
            warn_n += len(warns)
            for w in warns:
                if "unreviewed" in w.lower():
                    cats["unreviewed translation"] += 1
                elif "over-application" in w.lower() or "scope" in w.lower():
                    cats["scope / carve-out"] += 1
                elif "modality" in w.lower():
                    cats["modality mismatch"] += 1
                elif "evidence" in w.lower():
                    cats["missing evidence"] += 1
                elif "enforced_by" in w.lower():
                    cats["enforced_by"] += 1
                else:
                    cats["other"] += 1
        print(
            f"\nModel check signals on these files: {err_n} error(s), {warn_n} warning(s) "
            f"(coverage is a drafting aid, not assurance by itself)"
        )
        if cats:
            top = ", ".join(f"{n}× {k}" for k, n in cats.most_common(5))
            print(f"  top categories: {top}")
    return 0


def _collapse_messages(messages: list[str], kind: str) -> list[str]:
    """Collapse near-duplicate messages into counts (e.g. 11× unreviewed)."""
    from collections import Counter

    def key(msg: str) -> str:
        # strip contract[n] / id '…' prefixes for grouping
        m = re.sub(r"contract\[\d+\](\s+id\s+'[^']+')?:?\s*", "contract: ", msg)
        m = re.sub(r"\bid '[^']+'\b", "id '*'", m)
        return m

    counts = Counter(key(m) for m in messages)
    # preserve first-seen order
    seen: list[str] = []
    for m in messages:
        k = key(m)
        if k not in seen:
            seen.append(k)
    out: list[str] = []
    for k in seen:
        n = counts[k]
        if n == 1:
            # recover one original for readability
            for m in messages:
                if key(m) == k:
                    out.append(f"  {kind}: {m}")
                    break
        else:
            out.append(f"  {kind}: ({n}×) {k}")
    return out


def print_report(display: object, errors: list[str], warnings: list[str]) -> None:
    if not errors and not warnings:
        print(f"OK  {display}")
        return
    if errors:
        print(f"FAIL {display}")
    else:
        print(f"OK  {display} (with warnings)")
    for line in _collapse_messages(errors, "error"):
        print(line)
    for line in _collapse_messages(warnings, "warning"):
        print(line)


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
