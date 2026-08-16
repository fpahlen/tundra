"""In-memory interview sessions (dogfood: tundra-interview-session)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _contracts_have_ids(yaml_text: str) -> bool:
    """True if every Contract is an object with a non-empty id (preferred form)."""
    if not yaml_text.strip():
        return False
    try:
        import yaml  # local: same dep as checker

        doc = yaml.safe_load(yaml_text)
    except Exception:  # noqa: BLE001
        doc = None
    if isinstance(doc, dict):
        contracts = doc.get("contracts")
        if not contracts:
            return True  # nothing to id
        if not isinstance(contracts, list):
            return False
        for c in contracts:
            if isinstance(c, dict) and str(c.get("id") or "").strip():
                continue
            # bare string Contracts have no id
            return False
        return True
    # Fallback: list form `- id: foo` or nested `id: foo`
    return bool(re.search(r"(?m)^\s*-?\s*id:\s+\S+", yaml_text))


@dataclass
class Message:
    role: str  # author | facilitator | system
    content: str
    at: str = field(default_factory=_now)


@dataclass
class Session:
    id: str
    session_state: str = "Open"  # Open | Awaiting Author input | Abandoned
    draft_state: str = "Empty"  # Empty | Proposed | Structurally invalid|valid | Domain ready | Exported
    messages: list[Message] = field(default_factory=list)
    draft_yaml: str | None = None
    turn: int = 0
    last_validation: dict[str, Any] | None = None
    created_at: str = field(default_factory=_now)

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_state": self.session_state,
            "draft_state": self.draft_state,
            "turn": self.turn,
            "draft_yaml": self.draft_yaml,
            "last_validation": self.last_validation,
            "messages": [
                {"role": m.role, "content": m.content, "at": m.at} for m in self.messages
            ],
            "export_allowed": self.export_allowed(),
            "checklist": self.checklist(),
        }

    def export_allowed(self) -> bool:
        """export-when-domain-ready: structural ok + no open checklist fails."""
        if self.draft_state not in ("Structurally valid", "Domain ready", "Exported"):
            # allow export only when structurally valid at minimum for v0
            if self.draft_state != "Domain ready" and self.draft_state != "Structurally valid":
                return False
        if not self.draft_yaml:
            return False
        v = self.last_validation or {}
        if not v.get("ok"):
            return False
        # domain ready requires no critical checklist fails
        cl = self.checklist()
        return all(item["ok"] for item in cl if item.get("blocking"))

    def checklist(self) -> list[dict[str, Any]]:
        """Pre-export checklist (workflow W1)."""
        y = self.draft_yaml or ""
        v = self.last_validation or {}
        errors = v.get("errors") or []
        warnings = v.get("warnings") or []

        # Genesis: "nothing", "no X exist(s)", "X does/do not exist", "no X yet"
        has_genesis = bool(
            re.search(
                r"requires:\s*("
                r"nothing"
                r"|no \S+(?: \S+)? exists?"
                r"|.+ does not exist"
                r"|.+ do not exist"
                r"|no \S+(?: \S+)? yet"
                r")",
                y,
                re.I,
            )
        )
        # Contract ids: prefer real YAML parse (list form is `- id: foo`, not indented `id:`)
        has_ids = _contracts_have_ids(y)
        has_enforced = "enforced_by:" in y
        inferred = bool(re.search(r"source:\s*inferred", y, re.I))
        vague = [w for w in warnings if "vague" in w.lower() or "comparative" in w.lower()]

        items = [
            {
                "id": "structural",
                "label": "Structural schema check passes",
                "ok": bool(v.get("ok")) if v else False,
                "blocking": True,
                "detail": "; ".join(errors[:3]) if errors else "",
            },
            {
                "id": "genesis",
                "label": "Genesis Process present (no X exists / …)",
                "ok": has_genesis,
                "blocking": True,
                "detail": "" if has_genesis else "Add a Process that creates the subject",
            },
            {
                "id": "ids",
                "label": "Contracts use ids (preferred)",
                "ok": has_ids,
                "blocking": False,
                "detail": "" if has_ids else "Prefer id: + text on Contracts",
            },
            {
                "id": "enforced_by",
                "label": "Processes use enforced_by (preferred)",
                "ok": has_enforced,
                "blocking": False,
                "detail": "" if has_enforced else "Bind Contracts to Processes",
            },
            {
                "id": "inferred",
                "label": "No unconfirmed assumptions (source: inferred)",
                "ok": not inferred,
                "blocking": True,
                "detail": "Confirm or drop assumed rules before export" if inferred else "",
            },
            {
                "id": "vagueness",
                "label": "No comparative Contracts without numbers",
                "ok": len(vague) == 0,
                "blocking": True,
                "detail": vague[0] if vague else "",
            },
        ]
        return items

    def checklist_conversation_notes(self) -> str | None:
        """Soft plain-English lines for failing checklist items (chat, not labels)."""
        friendly = {
            "structural": (
                "The draft still has structural issues the checker flags — "
                "worth fixing before export."
            ),
            "genesis": (
                "We still need a clear “how this starts” step (genesis) — "
                "usually a first process with something like "
                "`requires: no Hours exist` (or `nothing`)."
            ),
            "ids": (
                "Contracts work better with short `id`s so we can point at them "
                "from processes and scenarios."
            ),
            "enforced_by": (
                "We haven’t linked Contracts to Processes yet "
                "(`enforced_by`) — that makes the rules easier to test."
            ),
            "inferred": (
                "I still have assumptions in the draft (highlighted on the right) — "
                "please confirm or drop them so we don’t export unstated rules."
            ),
            "vagueness": (
                "A rule still uses comparative wording without a number "
                "(hard to test as-is)."
            ),
        }
        fails = [it for it in self.checklist() if not it.get("ok")]
        if not fails:
            return None
        lines = [
            "**Things we haven’t settled yet** (also on the export checklist):",
            "",
        ]
        for it in fails:
            tip = friendly.get(it.get("id", ""), it.get("label", "Open checklist item"))
            detail = (it.get("detail") or "").strip()
            if detail and it.get("id") in ("structural", "vagueness"):
                tip = f"{tip} ({detail})"
            lines.append(f"- {tip}")
        return "\n".join(lines)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._order: list[str] = []

    def create(self) -> Session:
        sid = uuid.uuid4().hex[:12]
        s = Session(id=sid)
        s.messages.append(
            Message(
                role="facilitator",
                content=(
                    "Hi — walk me through a business process in plain language: "
                    "who does what, under which conditions, the happy path, and any "
                    "errors that matter. I’ll reframe it as a draft Tundra model on "
                    "the right; we can correct it together.\n\n"
                    "What process should we model?"
                ),
            )
        )
        self._sessions[sid] = s
        self._order.append(sid)
        return s

    def get(self, sid: str) -> Session | None:
        return self._sessions.get(sid)

    def list_ids(self) -> list[str]:
        return list(self._order)

    def last_id(self) -> str | None:
        return self._order[-1] if self._order else None

    def abandon(self, sid: str) -> Session | None:
        s = self._sessions.get(sid)
        if not s:
            return None
        s.session_state = "Abandoned"
        return s


store = SessionStore()
