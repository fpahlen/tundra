"""Write agent-readable session snapshots under web/debug/."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.llm import has_api_key
from app.paths import WEB_ROOT

if TYPE_CHECKING:
    from app.sessions import Session

DEBUG_DIR = WEB_ROOT / "debug"
LAST_PATH = DEBUG_DIR / "last-session.md"
LAST_ID_PATH = DEBUG_DIR / "last-session-id.txt"


def render_markdown(session: Session) -> str:
    """Full snapshot: conversation, draft, checklist, validation."""
    lines: list[str] = []
    lines.append(f"# Interview session `{session.id}`")
    lines.append("")
    lines.append("## Meta")
    lines.append("")
    lines.append(f"- **session_state:** {session.session_state}")
    lines.append(f"- **draft_state:** {session.draft_state}")
    lines.append(f"- **turn:** {session.turn}")
    lines.append(f"- **export_allowed:** {session.export_allowed()}")
    lines.append(f"- **llm:** {'live' if has_api_key() else 'demo'}")
    lines.append(f"- **created_at:** {session.created_at}")
    lines.append("")

    lines.append("## Conversation")
    lines.append("")
    if not session.messages:
        lines.append("_(no messages)_")
        lines.append("")
    else:
        for i, m in enumerate(session.messages, 1):
            who = m.role.upper()
            lines.append(f"### {i}. {who} ({m.at})")
            lines.append("")
            lines.append(m.content.rstrip() or "_(empty)_")
            lines.append("")

    lines.append("## Model draft")
    lines.append("")
    if session.draft_yaml:
        lines.append("```yaml")
        lines.append(session.draft_yaml.rstrip())
        lines.append("```")
    else:
        lines.append("_(no draft yet)_")
    lines.append("")

    lines.append("## Pre-export checklist")
    lines.append("")
    for item in session.checklist():
        mark = "OK" if item.get("ok") else "FAIL"
        block = "blocking" if item.get("blocking") else "optional"
        detail = item.get("detail") or ""
        line = f"- **[{mark}]** ({block}) {item.get('label', '')}"
        if detail:
            line += f" — {detail}"
        lines.append(line)
    lines.append("")

    lines.append("## Validation")
    lines.append("")
    v = session.last_validation
    if not v:
        lines.append("_(no validation run yet)_")
    else:
        lines.append(f"- **structural_ok:** {v.get('ok')}")
        errs = v.get("errors") or []
        warns = v.get("warnings") or []
        if errs:
            lines.append("- **errors:**")
            for e in errs:
                lines.append(f"  - {e}")
        else:
            lines.append("- **errors:** _(none)_")
        if warns:
            lines.append("- **warnings:**")
            for w in warns:
                lines.append(f"  - {w}")
        else:
            lines.append("- **warnings:** _(none)_")
    lines.append("")
    return "\n".join(lines)


def write_snapshot(session: Session) -> Path:
    """Write last-session.md and session-<id>.md; return path to last-session.md."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    md = render_markdown(session)
    LAST_PATH.write_text(md, encoding="utf-8")
    LAST_ID_PATH.write_text(session.id + "\n", encoding="utf-8")
    (DEBUG_DIR / f"session-{session.id}.md").write_text(md, encoding="utf-8")
    return LAST_PATH
