"""Semantic checks for Tundra models (lifecycle, scenarios, vagueness).

Used by check_tundra.py after schema validation. Pure functions: data in, messages out.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Comparative / scalar language — OK if a digit appears in the same Contract
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
GENESIS_REQUIRES = re.compile(
    r"^(nothing|"
    r"no .+\s+exists?|"
    r".+\s+does not exist|"
    r".+\s+do not exist)$",
    re.I,
)
STATE_SUBJECT = re.compile(r"\b(is|are|has|have)\b", re.I)


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def contract_text(entry: Any) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        text = entry.get("text")
        return text if isinstance(text, str) else None
    return None


def contract_id(entry: Any) -> str | None:
    if isinstance(entry, dict):
        cid = entry.get("id")
        return cid if isinstance(cid, str) else None
    return None


def collect_states(data: dict) -> tuple[list[str], list[dict]]:
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


def is_genesis_requires(req: str) -> bool:
    return bool(GENESIS_REQUIRES.match(req.strip()))


def state_subject(state_name: str) -> str:
    m = STATE_SUBJECT.search(state_name)
    if not m:
        return state_name.strip()
    return state_name[: m.start()].strip()


def process_result_states(proc: dict) -> list[str]:
    out: list[str] = []
    if proc.get("outcomes"):
        for branch in proc.get("outcomes") or []:
            if isinstance(branch, dict):
                for res in as_list(branch.get("results")):
                    if isinstance(res, str):
                        out.append(res)
    elif proc.get("results") is not None:
        for res in as_list(proc.get("results")):
            if isinstance(res, str):
                out.append(res)
    return out


def is_genesis_process(proc: dict) -> bool:
    reqs = [r for r in as_list(proc.get("requires")) if isinstance(r, str)]
    if not reqs:
        return False
    return all(is_genesis_requires(r) for r in reqs)


def process_can_fire(proc: dict, reachable: set[str]) -> bool:
    reqs = [r for r in as_list(proc.get("requires")) if isinstance(r, str)]
    if not reqs:
        return True
    state_reqs = [r for r in reqs if not is_genesis_requires(r)]
    if not state_reqs:
        return True
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


@dataclass
class ContractIndex:
    texts: list[str] = field(default_factory=list)
    ids: dict[str, str] = field(default_factory=dict)  # id -> text
    id_set: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)

    @property
    def text_set(self) -> set[str]:
        return set(self.texts)


def index_contracts(data: dict) -> ContractIndex:
    idx = ContractIndex()
    for i, c in enumerate(data.get("contracts") or []):
        ct = contract_text(c)
        cid = contract_id(c)
        if not ct:
            idx.errors.append(
                f"contract[{i}]: must be a string (or object with id + text)"
            )
            continue
        idx.texts.append(ct)
        if cid:
            if cid in idx.id_set:
                idx.errors.append(f"contract[{i}]: duplicate id {cid!r}")
            idx.id_set.add(cid)
            idx.ids[cid] = ct
    return idx


def classify_model_kind(
    data: dict,
    processes: list[dict],
    state_names: list[str],
) -> tuple[bool, bool, list[str]]:
    """Return (is_obligations, is_lifecycle, errors)."""
    errors: list[str] = []
    kind = data.get("kind")
    has_reg = isinstance(data.get("regulation"), dict)

    if kind == "obligations" and (processes or state_names):
        errors.append(
            "kind: obligations must not declare states or processes "
            "(remove them, or use kind: lifecycle / omit kind)"
        )

    is_obligations = kind == "obligations" or (
        has_reg and not processes and not state_names
    )
    if kind == "obligations":
        is_obligations = True
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
    return is_obligations, is_lifecycle, errors


@dataclass
class ProcessScan:
    actors_used: set[str] = field(default_factory=set)
    results_produced: set[str] = field(default_factory=set)
    requires_consumed: set[str] = field(default_factory=set)
    enforced_refs: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)


def check_processes(
    processes: list[dict],
    role_set: set[str],
    state_set: set[str],
    id_set: set[str],
) -> ProcessScan:
    scan = ProcessScan()
    for i, proc in enumerate(processes):
        if not isinstance(proc, dict):
            continue
        pname = proc.get("name", f"process[{i}]")
        actor = proc.get("actor")
        if actor and actor != "System" and actor not in role_set:
            scan.errors.append(
                f"process[{i}] ({pname!r}): actor {actor!r} is not in roles "
                f"and is not 'System'"
            )
        if isinstance(actor, str):
            scan.actors_used.add(actor)

        for req in as_list(proc.get("requires")):
            if not isinstance(req, str):
                continue
            if is_genesis_requires(req):
                continue
            if req not in state_set:
                scan.errors.append(
                    f"process[{i}] ({pname!r}): requires {req!r} is not a declared "
                    f"State and not a genesis condition "
                    f'(use a State name, or "nothing" / "no <Subject> exists")'
                )
            else:
                scan.requires_consumed.add(req)

        has_results = proc.get("results") is not None
        has_outcomes = proc.get("outcomes") is not None
        if has_results and has_outcomes:
            scan.errors.append(
                f"process[{i}] ({pname!r}): use either results or outcomes, not both"
            )
        if not has_results and not has_outcomes:
            scan.errors.append(
                f"process[{i}] ({pname!r}): must declare results (AND) or outcomes "
                f"(XOR branches)"
            )

        result_states: list[str] = []
        if has_results and not has_outcomes:
            for res in as_list(proc.get("results")):
                if not isinstance(res, str):
                    continue
                if res not in state_set:
                    scan.errors.append(
                        f"process[{i}] ({pname!r}): results {res!r} is not a "
                        f"declared State"
                    )
                else:
                    scan.results_produced.add(res)
                    result_states.append(res)
            subjects = [state_subject(s) for s in result_states]
            for sub in set(subjects):
                if sub and subjects.count(sub) >= 2:
                    scan.errors.append(
                        f"process[{i}] ({pname!r}): results lists multiple States of "
                        f"subject {sub!r} — results is AND; use outcomes: for "
                        f"exclusive branches"
                    )

        if has_outcomes:
            outcomes = proc.get("outcomes")
            if not isinstance(outcomes, list) or not outcomes:
                scan.errors.append(
                    f"process[{i}] ({pname!r}): outcomes must be a non-empty list"
                )
            else:
                otherwise_count = 0
                for bi, branch in enumerate(outcomes):
                    if not isinstance(branch, dict):
                        scan.errors.append(
                            f"process[{i}] ({pname!r}) outcomes[{bi}]: must be a mapping"
                        )
                        continue
                    when = branch.get("when")
                    if not isinstance(when, str) or not when.strip():
                        scan.errors.append(
                            f"process[{i}] ({pname!r}) outcomes[{bi}]: when is required"
                        )
                    elif when.strip().lower() == "otherwise":
                        otherwise_count += 1
                        if bi != len(outcomes) - 1:
                            scan.errors.append(
                                f"process[{i}] ({pname!r}): 'otherwise' branch must be last"
                            )
                    bres = as_list(branch.get("results"))
                    if not bres:
                        scan.errors.append(
                            f"process[{i}] ({pname!r}) outcomes[{bi}]: results required"
                        )
                    for res in bres:
                        if not isinstance(res, str):
                            continue
                        if res not in state_set:
                            scan.errors.append(
                                f"process[{i}] ({pname!r}) outcomes[{bi}]: "
                                f"results {res!r} is not a declared State"
                            )
                        else:
                            scan.results_produced.add(res)
                if otherwise_count > 1:
                    scan.errors.append(
                        f"process[{i}] ({pname!r}): at most one 'otherwise' outcome branch"
                    )

        for eid in as_list(proc.get("enforced_by")):
            if not isinstance(eid, str):
                continue
            if eid not in id_set:
                scan.errors.append(
                    f"process[{i}] ({pname!r}): enforced_by id {eid!r} is not a "
                    f"declared Contract id"
                )
            else:
                scan.enforced_refs.add(eid)
    return scan


@dataclass
class ScenarioScan:
    quoted_texts: set[str] = field(default_factory=set)
    quoted_ids: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def check_scenarios(
    data: dict,
    contract_text_set: set[str],
    id_set: set[str],
) -> ScenarioScan:
    scan = ScenarioScan()
    for i, scen in enumerate(data.get("scenarios") or []):
        if not isinstance(scen, dict):
            continue
        for j, step in enumerate(scen.get("steps") or []):
            if not isinstance(step, str):
                continue
            if not STEP_PREFIX.match(step.strip()):
                scan.warnings.append(
                    f"scenario[{i}] step[{j}]: does not start with "
                    f"Given/When/Then/And: {step!r}"
                )
            for m in CONTRACT_QUOTE.finditer(step):
                q = m.group(1)
                scan.quoted_texts.add(q)
                if q not in contract_text_set:
                    scan.errors.append(
                        f"scenario[{i}] step[{j}]: contract quote does not match "
                        f"any declared Contract text: {q!r}"
                    )
            for m in CONTRACT_ID_REF.finditer(step):
                qid = m.group(1)
                scan.quoted_ids.add(qid)
                if qid not in id_set:
                    scan.errors.append(
                        f"scenario[{i}] step[{j}]: contract id [{qid}] is not a "
                        f"declared Contract id"
                    )
    return scan


def check_contract_demonstration(
    data: dict,
    quoted_texts: set[str],
    quoted_ids: set[str],
    enforced_refs: set[str],
) -> list[str]:
    warnings: list[str] = []
    for i, c in enumerate(data.get("contracts") or []):
        ct = contract_text(c)
        cid = contract_id(c)
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
    return warnings


def check_enforced_by_usage(
    contract_ids: dict[str, str],
    enforced_refs: set[str],
    has_processes: bool,
    data: dict | None = None,
) -> list[str]:
    """Only nag about missing enforced_by for runtime_guard (or unset implement_as)."""
    if not has_processes or not contract_ids:
        return []
    impl_by_id: dict[str, str | None] = {}
    if data:
        for c in data.get("contracts") or []:
            if isinstance(c, dict) and isinstance(c.get("id"), str):
                impl_by_id[c["id"]] = c.get("implement_as")
    warnings: list[str] = []
    for cid, ct in contract_ids.items():
        if cid in enforced_refs:
            continue
        impl = impl_by_id.get(cid)
        # Non-runtime classes are not expected on Process enforced_by
        if impl in _SKIP_ENFORCED_BY_NAG:
            continue
        warnings.append(
            f"contract id {cid!r}: never listed in any Process enforced_by "
            f"({ct!r})"
        )
    return warnings


def check_lifecycle_reachability(
    processes: list[dict],
    state_names: list[str],
    state_objects: list[dict],
    state_set: set[str],
    results_produced: set[str],
    requires_consumed: set[str],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not processes:
        return errors, warnings

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
    return errors, warnings


def check_role_usage(
    roles: list[str],
    actors_used: set[str],
    contracts_text: list[str],
    is_lifecycle: bool,
    *,
    regulatory: bool = False,
) -> list[str]:
    """For regulatory models, prefer Contract-mention over Process-actor (duties > workflow)."""
    warnings: list[str] = []
    if regulatory or not is_lifecycle:
        for r in roles:
            if not any(r.lower() in (ct or "").lower() for ct in contracts_text):
                warnings.append(
                    f"role {r!r}: never named in any Contract "
                    f"(possible dropped duty in a regulatory translation)"
                )
    else:
        for r in roles:
            if r not in actors_used:
                warnings.append(
                    f"role {r!r}: never used as a Process actor "
                    f"(passive Role, or unused declaration)"
                )
    return warnings


def _norm_when(step: str) -> str:
    s = step.strip().lower()
    s = re.sub(r"^when\s+", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def demonstrated_contract_keys(
    data: dict,
) -> tuple[set[str], set[str], list[str]]:
    """
    Stricter "assurance demonstrated" bar (reviews 5–6):

    A Contract counts as demonstrated only if:
    1. A Scenario has a **failure** step for it (`is broken`), AND
    2. It has `evidence:` OR `enforced_by` OR `implemented_at:`, AND
    3. Its failure Scenario's When step is not a duplicate of another Contract's
       (eleven copies of "When it does not comply" count as one test).

    Returns (dem_ids, dem_texts, warnings).
    """
    warnings: list[str] = []
    # contract_id / text -> list of when-hashes from its break scenarios
    break_whens: dict[str, list[str]] = {}
    broken_texts: set[str] = set()
    broken_ids: set[str] = set()

    for scen in data.get("scenarios") or []:
        if not isinstance(scen, dict):
            continue
        when_step = ""
        break_ids: list[str] = []
        break_texts: list[str] = []
        for step in scen.get("steps") or []:
            if not isinstance(step, str):
                continue
            st = step.strip()
            if re.match(r"(?i)^when\b", st):
                when_step = st
            low = st.lower()
            if "is broken" not in low:
                continue
            for m in CONTRACT_QUOTE.finditer(st):
                break_texts.append(m.group(1))
                broken_texts.add(m.group(1))
            for m in CONTRACT_ID_REF.finditer(st):
                break_ids.append(m.group(1))
                broken_ids.add(m.group(1))
        wh = _norm_when(when_step) if when_step else ""
        for cid in break_ids:
            break_whens.setdefault(f"id:{cid}", []).append(wh)
        for tx in break_texts:
            break_whens.setdefault(f"text:{tx}", []).append(wh)

    # Detect shared When conditions across different contracts
    when_to_keys: dict[str, set[str]] = {}
    for key, whens in break_whens.items():
        for w in whens:
            if not w:
                continue
            when_to_keys.setdefault(w, set()).add(key)
    shared_whens = {w: ks for w, ks in when_to_keys.items() if len(ks) > 1}
    if shared_whens:
        # one warning listing count
        n = sum(len(ks) for ks in shared_whens.values())
        warnings.append(
            f"demonstrated coverage: {len(shared_whens)} duplicated When condition(s) "
            f"shared across {n} contract failure scenarios "
            f"(identical Whens count as one test — vary the failure condition)"
        )

    enforced: set[str] = set()
    for proc in data.get("processes") or []:
        if not isinstance(proc, dict):
            continue
        for eid in as_list(proc.get("enforced_by")):
            if isinstance(eid, str):
                enforced.add(eid)

    dem_ids: set[str] = set()
    dem_texts: set[str] = set()
    # Contracts that only share a When with others: still allow one winner per When
    claimed_whens: set[str] = set()

    for c in data.get("contracts") or []:
        if not isinstance(c, dict):
            continue
        ct = contract_text(c)
        cid = contract_id(c)
        if not ct:
            continue
        has_break = ct in broken_texts or (cid is not None and cid in broken_ids)
        has_evidence = bool(c.get("evidence"))
        has_enforced = bool(cid and cid in enforced)
        has_impl_at = bool(
            isinstance(c.get("implemented_at"), str)
            and str(c.get("implemented_at", "")).strip()
        )
        has_hook = has_evidence or has_enforced or has_impl_at
        if not (has_break and has_hook):
            continue
        # unique When: prefer contract's own when list
        keys = []
        if cid:
            keys.extend(break_whens.get(f"id:{cid}", []))
        keys.extend(break_whens.get(f"text:{ct}", []))
        unique_when = None
        for w in keys:
            if w and w not in claimed_whens:
                unique_when = w
                break
            if w and w not in shared_whens:
                unique_when = w
                break
        if keys and all(w in shared_whens for w in keys if w):
            # all whens shared — only first contract claiming each when gets credit
            for w in keys:
                if w and w not in claimed_whens:
                    unique_when = w
                    break
            if unique_when is None:
                continue
        if unique_when:
            claimed_whens.add(unique_when)
        elif keys:
            # empty when steps — allow but weak
            pass
        if cid:
            dem_ids.add(cid)
        dem_texts.add(ct)
    return dem_ids, dem_texts, warnings


def check_expires_handlers(
    processes: list[dict], expires_states: list[str]
) -> list[str]:
    warnings: list[str] = []
    if not processes:
        return warnings
    for name in expires_states:
        has_handler = False
        for proc in processes:
            if proc.get("actor") != "System":
                continue
            reqs = as_list(proc.get("requires"))
            if name in reqs:
                has_handler = True
                break
        if not has_handler:
            warnings.append(
                f"state {name!r}: has expires_in but no System Process lists it "
                f"in requires (timer with no handler)"
            )
    return warnings


def check_state_subjects(state_names: list[str]) -> list[str]:
    errors: list[str] = []
    for i, name in enumerate(state_names):
        if not STATE_SUBJECT.search(name):
            errors.append(
                f"state[{i}] {name!r}: every State must name its subject "
                f'(e.g. "Hours are in Draft", not "Draft")'
            )
    return errors


# Non-process-hook implement_as values
_NON_RUNTIME = frozenset({"recorded_control", "capability", "governance"})
_SKIP_ENFORCED_BY_NAG = _NON_RUNTIME | frozenset({"proportionality", "permission"})

_EVIDENCE_TYPES = frozenset(
    {
        "board_minutes",
        "training_record",
        "policy",
        "contract_clause",
        "log_export",
        "attestation",
        "register",
        "test_result",
        "other",
    }
)


def check_implement_as_hints(data: dict) -> list[str]:
    """
    - runtime_guard needs enforced_by OR implemented_at (esp. under kind: obligations)
    - non-runtime classes need evidence:
    - warn translation_review: unreviewed
    """
    warnings: list[str] = []
    kind = data.get("kind")
    enforced: set[str] = set()
    for proc in data.get("processes") or []:
        if not isinstance(proc, dict):
            continue
        for eid in as_list(proc.get("enforced_by")):
            if isinstance(eid, str):
                enforced.add(eid)

    for i, c in enumerate(data.get("contracts") or []):
        if not isinstance(c, dict):
            continue
        impl = c.get("implement_as")
        cid = contract_id(c)
        impl_at = c.get("implemented_at")
        has_impl_at = isinstance(impl_at, str) and impl_at.strip()

        if impl in _NON_RUNTIME:
            ev = c.get("evidence")
            if not ev or not isinstance(ev, list) or len(ev) == 0:
                warnings.append(
                    f"contract[{i}]"
                    + (f" id {cid!r}" if cid else "")
                    + f": implement_as is {impl!r} but evidence: is empty "
                    f"(non-runtime controls need artefacts a supervisor could ask for)"
                )
            else:
                for j, item in enumerate(ev):
                    if not isinstance(item, dict):
                        continue
                    et = item.get("type")
                    if et not in _EVIDENCE_TYPES:
                        warnings.append(
                            f"contract[{i}] evidence[{j}]: type {et!r} not in "
                            f"controlled vocabulary {_EVIDENCE_TYPES}"
                        )
                    if et == "other":
                        desc = item.get("description") or ""
                        if len(str(desc).strip()) < 40:
                            warnings.append(
                                f"contract[{i}] evidence[{j}]: type other requires "
                                f"description ≥ 40 characters (not a mood word)"
                            )

        if impl == "runtime_guard":
            if cid and cid in enforced:
                pass
            elif has_impl_at:
                pass
            elif kind == "obligations":
                warnings.append(
                    f"contract[{i}] id {cid!r}: implement_as is runtime_guard under "
                    f"kind: obligations — set implemented_at: (code/system symbol) "
                    f"or use recorded_control/capability/governance with evidence:"
                )
            elif cid:
                warnings.append(
                    f"contract[{i}] id {cid!r}: implement_as is runtime_guard but no Process "
                    f"lists it in enforced_by and implemented_at: is unset"
                )

        tr = c.get("translation_review")
        if isinstance(tr, dict) and tr.get("status") == "unreviewed":
            warnings.append(
                f"contract[{i}]"
                + (f" id {cid!r}" if cid else "")
                + ": translation_review.status is unreviewed "
                f"(sign-off still open)"
            )
    return warnings


def check_vagueness(
    data: dict,
    roles: list[str],
    state_names: list[str],
) -> list[str]:
    warnings: list[str] = []
    for i, c in enumerate(data.get("contracts") or []):
        contract = contract_text(c) or ""
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
    return warnings


def check_system_not_a_role(roles: list[str]) -> list[str]:
    if "System" in roles:
        return [
            "roles: do not declare 'System' as a Role — use actor: System on Processes "
            "without listing System under roles (see tundra.md)"
        ]
    return []
