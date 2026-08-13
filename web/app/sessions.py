"""In-memory interview sessions (dogfood: tundra-interview-session)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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

        has_genesis = bool(
            re.search(
                r"requires:\s*(nothing|no .+ exists|.+ does not exist)",
                y,
                re.I,
            )
        )
        has_ids = bool(re.search(r"(?m)^\s+id:\s+\S+", y))
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
                "label": "No unconfirmed source: inferred",
                "ok": not inferred,
                "blocking": True,
                "detail": "Confirm or remove inferred Contracts" if inferred else "",
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
                    "Session started. Describe a business process in plain language "
                    "(who does what, under which conditions, happy path and important errors). "
                    "I will reframe it as a Tundra model for you to correct.\n\n"
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
