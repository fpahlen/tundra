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
        r"\bcorrectly\b",
        r"\bpromptly\b",
    ]
]

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
    """Discover models for --all."""
    paths: list[Path] = []
    for sub in ("models", "examples"):
        d = ROOT / sub
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*.tundra")):
            # Negative fixtures for the checker itself (must FAIL when run alone)
            if "bad-structure" in p.parts:
                continue
            paths.append(p)
    skill_ex = ROOT / ".grok" / "skills" / "tundra" / "references" / "example.tundra"
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

        for res in _as_list(proc.get("results")):
            if not isinstance(res, str):
                continue
            if res not in state_set:
                errors.append(
                    f"process[{i}] ({pname!r}): results {res!r} is not a declared State"
                )
            else:
                results_produced.add(res)

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

    # If any contract has an id, warn ids never enforced_by any process
    if id_set:
        for cid, ct in contract_ids.items():
            if cid not in enforced_refs:
                warnings.append(
                    f"contract id {cid!r}: never listed in any Process enforced_by "
                    f"({ct!r})"
                )

    # Unproduced states (warn — may be intentional initial states)
    for name in state_names:
        if name not in results_produced:
            warnings.append(
                f"state {name!r}: never appears in any Process results "
                f"(dead state, or intentional initial-only state)"
            )

    # Roles never used as actor (warn — passive Roles may be intentional)
    for r in roles:
        if r not in actors_used:
            warnings.append(
                f"role {r!r}: never used as a Process actor "
                f"(passive Role, or unused declaration)"
            )

    # expires_in without System process that requires that state
    for name in expires_states:
        has_handler = False
        for proc in data.get("processes") or []:
            if not isinstance(proc, dict):
                continue
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

    # Vague contracts (warn)
    for i, contract in enumerate(contracts_text):
        for pat in VAGUE_PATTERNS:
            if pat.search(contract):
                warnings.append(
                    f"contract[{i}]: possibly vague phrasing ({pat.pattern}): {contract!r}"
                )
                break

    return errors, warnings


def is_genesis_requires(req: str) -> bool:
    return bool(GENESIS_REQUIRES.match(req.strip()))


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
