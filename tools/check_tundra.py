#!/usr/bin/env python3
"""Checker for Tundra models (YAML in .tundra files).

Enforces schema plus semantic links the format depends on:
contract quotes, requires/results vs states, subject-named states, etc.
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

# Comparative / scalar language — OK if a digit appears in the same Contract
# Prefer multi-word cues so "more detail" is not flagged; "more than 24" is OK via digit.
COMPARATIVE_CUES = re.compile(
    r"("
    r"\btoo high\b|\btoo low\b|"
    r"\bhigh relative to\b|\blow relative to\b|\brelative to\b|"
    r"\bmore than\b|\bless than\b|\bgreater than\b|\bfewer than\b|"
    r"\bhigher than\b|\blower than\b|"
    r"\babove\b|\bbelow\b|"
    r"\breasonable\b|\bsufficient\b|\bappropriate\b|\bsoon\b|\bpromptly\b|"
    r"\bfalls? between\b|\bfall between\b"
    r")",
    re.I,
)
HAS_DIGIT = re.compile(r"\d")

STEP_PREFIX = re.compile(r"^(Given|When|Then|And)\b")
CONTRACT_QUOTE = re.compile(
    r"""contract\s+["']([^"']+)["']\s+is\s+(broken|applied)""",
    re.I,
)
CONTRACT_ID_REF = re.compile(
    r"""contract\s+\[([a-z][a-z0-9_-]*)\]\s+is\s+(broken|applied)""",
    re.I,
)
# Genesis / pre-subject conditions (not declared States)
GENESIS_REQUIRES = re.compile(
    r"^(nothing|"
    r"no .+\s+exists?|"
    r".+\s+does not exist|"
    r".+\s+do not exist)$",
    re.I,
)
# "Subject is/are/has …" (subject-named States)
STATE_SUBJECT = re.compile(r"\b(is|are|has|have)\b", re.I)


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
            # Negative fixtures (run explicitly in CI, not in --all product corpus)
            if "bad-structure" in p.parts or "bad-contracts" in p.parts:
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


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _state_name(entry) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        name = entry.get("name")
        return name if isinstance(name, str) else None
    return None


def _contract_text(entry) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        text = entry.get("text")
        return text if isinstance(text, str) else None
    return None


def _contract_id(entry) -> str | None:
    if isinstance(entry, dict):
        cid = entry.get("id")
        return cid if isinstance(cid, str) else None
    return None


def _collect_states(data: dict) -> tuple[list[str], list[dict]]:
    names: list[str] = []
    objects: list[dict] = []
    for entry in data.get("states") or []:
        if isinstance(entry, dict):
            objects.append(entry)
            n = entry.get("name")
            if isinstance(n, str):
                names.append(n)
        elif isinstance(entry, str):
            names.append(entry)
    return names, objects


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

    if "System" in role_set:
        errors.append(
            "roles: do not declare 'System' as a Role — use actor: System on Processes "
            "without listing System under roles (see tundra.md)"
        )

    state_names, state_objects = _collect_states(data)
    state_set = set(state_names)

    contracts_text: list[str] = []
    contract_ids: dict[str, str] = {}  # id -> text
    id_set: set[str] = set()
    for i, c in enumerate(data.get("contracts") or []):
        ct = _contract_text(c)
        cid = _contract_id(c)
        if not ct:
            errors.append(f"contract[{i}]: must be a string (or object with id + text)")
            continue
        contracts_text.append(ct)
        if cid:
            if cid in id_set:
                errors.append(f"contract[{i}]: duplicate id {cid!r}")
            id_set.add(cid)
            contract_ids[cid] = ct
    contract_text_set = set(contracts_text)

    # State names subject
    for i, name in enumerate(state_names):
        if not STATE_SUBJECT.search(name):
            errors.append(
                f"state[{i}] {name!r}: every State must name its subject "
                f'(e.g. "Hours are in Draft", not "Draft")'
            )

    # Roles used as actors
    actors_used: set[str] = set()
    results_produced: set[str] = set()
    requires_consumed: set[str] = set()
    expires_states: list[str] = []
    enforced_refs: set[str] = set()  # contract ids referenced by processes

    for entry in state_objects:
        name = entry.get("name")
        if isinstance(name, str) and "expires_in" in entry:
            expires_states.append(name)

    for i, proc in enumerate(data.get("processes") or []):
        if not isinstance(proc, dict):
            continue
        pname = proc.get("name", f"process[{i}]")
        actor = proc.get("actor")
        if actor and actor != "System" and actor not in role_set:
            errors.append(
                f"process[{i}] ({pname!r}): actor {actor!r} is not in roles "
                f"and is not 'System'"
            )
        if isinstance(actor, str):
            actors_used.add(actor)

        for req in _as_list(proc.get("requires")):
            if not isinstance(req, str):
                continue
            if is_genesis_requires(req):
                continue
            if req not in state_set:
                errors.append(
                    f"process[{i}] ({pname!r}): requires {req!r} is not a declared "
                    f"State and not a genesis condition "
                    f'(use a State name, or "nothing" / "no <Subject> exists")'
                )
            else:
                requires_consumed.add(req)

        has_results = proc.get("results") is not None
        has_outcomes = proc.get("outcomes") is not None
        if has_results and has_outcomes:
            errors.append(
                f"process[{i}] ({pname!r}): use either results or outcomes, not both"
            )
        if not has_results and not has_outcomes:
            errors.append(
                f"process[{i}] ({pname!r}): must declare results (AND) or outcomes (XOR branches)"
            )

        result_states: list[str] = []
        if has_results and not has_outcomes:
            for res in _as_list(proc.get("results")):
                if not isinstance(res, str):
                    continue
                if res not in state_set:
                    errors.append(
                        f"process[{i}] ({pname!r}): results {res!r} is not a declared State"
                    )
                else:
                    results_produced.add(res)
                    result_states.append(res)
            # Same-subject multi-results almost always means exclusive branches (use outcomes)
            subjects = [state_subject(s) for s in result_states]
            for sub in set(subjects):
                if sub and subjects.count(sub) >= 2:
                    errors.append(
                        f"process[{i}] ({pname!r}): results lists multiple States of "
                        f"subject {sub!r} — results is AND; use outcomes: for exclusive branches"
                    )

        if has_outcomes:
            outcomes = proc.get("outcomes")
            if not isinstance(outcomes, list) or not outcomes:
                errors.append(f"process[{i}] ({pname!r}): outcomes must be a non-empty list")
            else:
                otherwise_count = 0
                for bi, branch in enumerate(outcomes):
                    if not isinstance(branch, dict):
                        errors.append(
                            f"process[{i}] ({pname!r}) outcomes[{bi}]: must be a mapping"
                        )
                        continue
                    when = branch.get("when")
                    if not isinstance(when, str) or not when.strip():
                        errors.append(
                            f"process[{i}] ({pname!r}) outcomes[{bi}]: when is required"
                        )
                    elif when.strip().lower() == "otherwise":
                        otherwise_count += 1
                        if bi != len(outcomes) - 1:
                            errors.append(
                                f"process[{i}] ({pname!r}): 'otherwise' branch must be last"
                            )
                    bres = _as_list(branch.get("results"))
                    if not bres:
                        errors.append(
                            f"process[{i}] ({pname!r}) outcomes[{bi}]: results required"
                        )
                    for res in bres:
                        if not isinstance(res, str):
                            continue
                        if res not in state_set:
                            errors.append(
                                f"process[{i}] ({pname!r}) outcomes[{bi}]: "
                                f"results {res!r} is not a declared State"
                            )
                        else:
                            results_produced.add(res)
                if otherwise_count > 1:
                    errors.append(
                        f"process[{i}] ({pname!r}): at most one 'otherwise' outcome branch"
                    )

        for eid in _as_list(proc.get("enforced_by")):
            if not isinstance(eid, str):
                continue
            if eid not in id_set:
                errors.append(
                    f"process[{i}] ({pname!r}): enforced_by id {eid!r} is not a "
                    f"declared Contract id"
                )
            else:
                enforced_refs.add(eid)

    # Scenario steps + contract quotes / ids
    quoted_texts: set[str] = set()
    quoted_ids: set[str] = set()
    for i, scen in enumerate(data.get("scenarios") or []):
        if not isinstance(scen, dict):
            continue
        for j, step in enumerate(scen.get("steps") or []):
            if not isinstance(step, str):
                continue
            if not STEP_PREFIX.match(step.strip()):
                warnings.append(
                    f"scenario[{i}] step[{j}]: does not start with "
                    f"Given/When/Then/And: {step!r}"
                )
            for m in CONTRACT_QUOTE.finditer(step):
                q = m.group(1)
                quoted_texts.add(q)
                if q not in contract_text_set:
                    errors.append(
                        f"scenario[{i}] step[{j}]: contract quote does not match "
                        f"any declared Contract text: {q!r}"
                    )
            for m in CONTRACT_ID_REF.finditer(step):
                qid = m.group(1)
                quoted_ids.add(qid)
                if qid not in id_set:
                    errors.append(
                        f"scenario[{i}] step[{j}]: contract id [{qid}] is not a "
                        f"declared Contract id"
                    )

    # Contract coverage (warn): demonstrated via quote, id, or enforced_by
    for i, c in enumerate(data.get("contracts") or []):
        ct = _contract_text(c)
        cid = _contract_id(c)
        if not ct:
            continue
        demonstrated = ct in quoted_texts
        if cid and (cid in quoted_ids or cid in enforced_refs):
            demonstrated = True
        if not demonstrated:
            warnings.append(
                f"contract[{i}]: never demonstrated in a Scenario "
                f'(quote text, or "[id] is broken/applied") and not listed in '
                f"any process enforced_by: {ct!r}"
            )

    processes = [p for p in (data.get("processes") or []) if isinstance(p, dict)]
    kind = data.get("kind")
    has_reg = isinstance(data.get("regulation"), dict)
    is_obligations = kind == "obligations" or (has_reg and not processes)
    is_lifecycle = not is_obligations

    if is_lifecycle:
        if not processes:
            errors.append(
                "lifecycle model has no processes "
                "(add Processes, or set kind: obligations for standing duties only)"
            )
        if not state_names:
            errors.append(
                "lifecycle model has no states "
                "(declare States, or set kind: obligations for standing duties only)"
            )

    # If any contract has an id, warn ids never enforced_by any process
    if id_set and processes:
        for cid, ct in contract_ids.items():
            if cid not in enforced_refs:
                warnings.append(
                    f"contract id {cid!r}: never listed in any Process enforced_by "
                    f"({ct!r})"
                )

    # Reachability from genesis — lifecycle models only
    if is_lifecycle and processes:
        genesis_procs = [p for p in processes if is_genesis_process(p)]
        if not genesis_procs:
            errors.append(
                "model has no genesis Process (no Process with requires like "
                '"nothing" / "no <Subject> exists" / "<Subject> does not exist"). '
                "Without one, no subject can come into existence. "
                "For standing duties with no lifecycle, set kind: obligations."
            )
        reachable = compute_reachable_states(processes, state_set)
        for name in state_names:
            if name not in reachable:
                warnings.append(
                    f"state {name!r}: not reachable from any genesis Process "
                    f"(unreachable lifecycle state)"
                )

        # Produced but never required — terminal or missing follow-up
        final_states: set[str] = set()
        for entry in state_objects:
            if isinstance(entry, dict) and entry.get("final") is True:
                n = entry.get("name")
                if isinstance(n, str):
                    final_states.add(n)
        for name in state_names:
            if name in results_produced and name not in requires_consumed:
                if name in final_states:
                    continue
                warnings.append(
                    f"state {name!r}: produced by a Process but never appears in any "
                    f"requires (terminal end-state, or missing follow-up Process; "
                    f"mark final: true on the state object if intentional)"
                )

    # Roles never used as actor (lifecycle) or never named in a Contract (obligations)
    if is_lifecycle:
        for r in roles:
            if r not in actors_used:
                warnings.append(
                    f"role {r!r}: never used as a Process actor "
                    f"(passive Role, or unused declaration)"
                )
    else:
        for r in roles:
            if not any(r.lower() in (ct or "").lower() for ct in contracts_text):
                warnings.append(
                    f"role {r!r}: never named in any Contract "
                    f"(possible dropped duty in a regulatory translation)"
                )

    # expires_in without System process that requires that state
    if processes:
        for name in expires_states:
            has_handler = False
            for proc in processes:
                if proc.get("actor") != "System":
                    continue
                reqs = _as_list(proc.get("requires"))
                if name in reqs:
                    has_handler = True
                    break
            if not has_handler:
                warnings.append(
                    f"state {name!r}: has expires_in but no System Process lists it "
                    f"in requires (timer with no handler)"
                )

    # Vagueness: comparative cue without a digit; Contract with no Role/State token
    # Skip digit heuristic when Contract carries legal cite (quote is authority)
    for i, c in enumerate(data.get("contracts") or []):
        contract = _contract_text(c) or ""
        has_cite = isinstance(c, dict) and bool(c.get("cite"))
        if (
            not has_cite
            and COMPARATIVE_CUES.search(contract)
            and not HAS_DIGIT.search(contract)
        ):
            warnings.append(
                f"contract[{i}]: comparative or vague wording without a number "
                f'(e.g. prefer "above 40%" over "high relative to"): {contract!r}'
            )
        cl = contract.lower()
        mentions_role = any(role.lower() in cl for role in roles)
        mentions_state = any(st.lower() in cl for st in state_names)
        subjects = set()
        for st in state_names:
            m = STATE_SUBJECT.search(st)
            if m:
                subjects.add(st[: m.start()].strip().lower())
        mentions_subject = any(sub and sub in cl for sub in subjects)
        if not mentions_role and not mentions_state and not mentions_subject:
            warnings.append(
                f"contract[{i}]: names no declared Role or State "
                f"(hard to test): {contract!r}"
            )

    # --- Regulatory provenance (shape + quote/article resolution) ---
    from cite_resolve import check_provenance  # noqa: WPS433

    pe, pw = check_provenance(data, path, ROOT)
    errors.extend(pe)
    warnings.extend(pw)

    return errors, warnings


def is_genesis_requires(req: str) -> bool:
    return bool(GENESIS_REQUIRES.match(req.strip()))


def state_subject(state_name: str) -> str:
    """Subject phrase before is/are/has/have."""
    m = STATE_SUBJECT.search(state_name)
    if not m:
        return state_name.strip()
    return state_name[: m.start()].strip()


def process_result_states(proc: dict) -> list[str]:
    """All State names this Process can produce (results AND or all outcome branches)."""
    out: list[str] = []
    if proc.get("outcomes"):
        for branch in proc.get("outcomes") or []:
            if isinstance(branch, dict):
                for res in _as_list(branch.get("results")):
                    if isinstance(res, str):
                        out.append(res)
    elif proc.get("results") is not None:
        for res in _as_list(proc.get("results")):
            if isinstance(res, str):
                out.append(res)
    return out


def is_genesis_process(proc: dict) -> bool:
    """True if every requires entry is a genesis condition (subject not yet existing)."""
    reqs = [r for r in _as_list(proc.get("requires")) if isinstance(r, str)]
    if not reqs:
        return False
    return all(is_genesis_requires(r) for r in reqs)


def process_can_fire(proc: dict, reachable: set[str]) -> bool:
    """requires list = OR: fire if any non-genesis require is reachable, or genesis-only."""
    reqs = [r for r in _as_list(proc.get("requires")) if isinstance(r, str)]
    if not reqs:
        return True
    state_reqs = [r for r in reqs if not is_genesis_requires(r)]
    if not state_reqs:
        return True  # pure genesis
    return any(r in reachable for r in state_reqs)


def compute_reachable_states(processes: list[dict], state_set: set[str]) -> set[str]:
    reachable: set[str] = set()
    changed = True
    while changed:
        changed = False
        for proc in processes:
            if not process_can_fire(proc, reachable):
                continue
            for res in process_result_states(proc):
                if res in state_set and res not in reachable:
                    reachable.add(res)
                    changed = True
    return reachable


def run_coverage(target: Path, yaml) -> int:
    """Print instrument coverage for a regulations sample directory."""
    from cite_resolve import cites_from_models, enumerate_source_coverage

    if target.is_file():
        model_paths = [target]
        sources_dir = target.parent / "sources"
    else:
        model_paths = sorted(target.rglob("*.tundra"))
        # prefer <target>/sources or <target>/**/sources next to models
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
        para = c.get("paragraph") or ""
        m = re.match(r"^(\d+)\s*\(([a-z])\)", para, re.I)
        if m:
            cited_paras.setdefault(art, set()).add(m.group(1))
            cited_points.setdefault(art, set()).add(m.group(2).lower())
        elif re.match(r"^\d+$", para):
            cited_paras.setdefault(art, set()).add(para)
        elif art:
            cited_paras.setdefault(art, set())

    total_p = total_pc = total_pts = total_ptc = 0
    print(f"Coverage for {sources_dir} ({len(model_paths)} model file(s))\n")
    for art in sorted(inventory.keys(), key=lambda x: int(x) if x.isdigit() else x):
        inv = inventory[art]
        paras = inv["paragraphs"]
        points = inv["points"]
        cp = cited_paras.get(art, set()) & paras if paras else cited_paras.get(art, set())
        # count paragraph hits even if parse missed
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
            print("usage: check_tundra.py --coverage <regulations-dir-or-model>", file=sys.stderr)
            return 2
        return run_coverage(args.paths[0], yaml)

    if not SCHEMA_PATH.is_file():
        print(f"Schema not found: {SCHEMA_PATH}", file=sys.stderr)
        return 2

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    if args.all or not args.paths:
        paths = find_models()
        # Negative fixtures are not part of the product corpus
        paths = [p for p in paths if "_fixtures" not in p.parts]
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
