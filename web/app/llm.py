"""LLM client (OpenAI-compatible) + demo facilitator."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

from app.paths import EXTRACT_PROMPT, FORMAT_MD, TUNDRA_MD

YAML_FENCE = re.compile(r"```(?:yaml|tundra|yml)?\s*\n.*?```", re.S | re.I)


def load_system_prompt() -> str:
    """System prompt for the web dual-panel Facilitator."""
    parts = [
        EXTRACT_PROMPT.read_text(encoding="utf-8"),
        "\n\n---\n# tundra.md (language definition)\n\n",
    ]
    if TUNDRA_MD.is_file():
        parts.append(TUNDRA_MD.read_text(encoding="utf-8"))
    elif FORMAT_MD.is_file():
        parts.append(FORMAT_MD.read_text(encoding="utf-8"))

    parts.append(
        """

---
# Web interview UI — dual channel (mandatory)

You are the Facilitator in a **two-panel** web interview:

| Panel | Content |
| --- | --- |
| **Conversation (left)** | What the Author *reads as chat* — **plain English only** |
| **Model draft (right)** | The `.tundra` YAML — machine artifact |

## What you must produce each turn

1. **Spoken reply (plain English first)** — like two humans talking:
   - Interpret what the model captures (who may do what, lifecycle, key rules).
   - Note what you deliberately left out and why.
   - List open gaps in short prose (not a wall of structure labels if avoidable).
   - End with an **open** question (“What other questions do you have?” /
     “What did I get wrong or leave out?”).
   - On later turns, explain **what changed** in plain English (not a YAML dump).
   - Do **not** paste the full model as the main chat message.
   - Do **not** open with a ```yaml fence.

2. **Hidden machine block (required, after the English)** — exactly one fenced block
   so the server can update the right-hand draft:

```yaml
tundra: …
# full model here
```

The UI **strips** that fence from chat and shows it only in the Model draft panel.
If you omit the fence, the draft will not update.

## Modelling rules (unchanged)

Never invent measurable thresholds. Prefer Contract ids and enforced_by.
Genesis Process required. Use outcomes for exclusive branches.
Mark inferred Contracts with source: inferred.
"""
    )
    return "".join(parts)


def demo_reply(user_message: str, turn: int, prior_yaml: str | None) -> str:
    """Deterministic facilitator when no API key is set (English + yaml fence)."""
    first = user_message.strip().split("\n")[0][:60] or "business process"
    slug = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")[:40] or "process"

    draft = f"""tundra: Interview draft ({slug})

roles:
  - Author
  - Clerk

relationships:
  - Author is Owner of Case
  - Clerk is Handler of Case

contracts:
  - id: only-author-starts
    text: Only the Author may start a Case
    source: inferred
  - id: only-clerk-handles
    text: Only a Clerk may advance a Case after it is Submitted
    source: inferred

states:
  - Case is Draft
  - Case is Submitted
  - name: Case is Closed
    final: true

processes:
  - name: Open Case
    actor: Author
    requires: no Case exists
    results: Case is Draft
    enforced_by:
      - only-author-starts
  - name: Submit Case
    actor: Author
    requires: Case is Draft
    results: Case is Submitted
  - name: Close Case
    actor: Clerk
    requires: Case is Submitted
    results: Case is Closed
    enforced_by:
      - only-clerk-handles

scenarios:
  - name: "Happy path: submit and close"
    steps:
      - Given no Case exists
      - When the Author opens a Case
      - Then the Case is Draft
      - When the Author submits the Case
      - Then the Case is Submitted
      - When the Clerk closes the Case
      - Then the Case is Closed
"""

    if turn <= 1 or not prior_yaml:
        english = (
            f"Here's how I understood it (demo mode — add XAI_API_KEY in web/.env for a live model).\n\n"
            f"You're describing a simple case lifecycle: the Author opens a case, can work on it "
            f"while it's in draft, then submits it. After that a Clerk can close it. "
            f"I treated “{first}\" as the starting description and kept the model thin.\n\n"
            f"Two Contracts are marked inferred — please confirm or correct them.\n\n"
            f"What other questions do you have?"
        )
        return f"{english}\n\n```yaml\n{draft.strip()}\n```\n"

    note = user_message.strip()[:160]
    english = (
        f"I've taken your latest note into account: {note!r}.\n\n"
        f"The draft model on the right is unchanged in demo mode except as a placeholder — "
        f"with a live key I would revise the YAML to match. Please confirm any inferred rules "
        f"or tell me what to add (e.g. cancellation, disputes).\n\n"
        f"What did I get wrong or leave out?"
    )
    body = (prior_yaml or draft).strip()
    return f"{english}\n\n```yaml\n{body}\n```\n"


async def chat_completion(messages: list[dict[str, str]]) -> str:
    """Call OpenAI-compatible Chat Completions API."""
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No API key")

    base = os.environ.get("TUNDRA_LLM_BASE_URL")
    if not base:
        if os.environ.get("XAI_API_KEY"):
            base = "https://api.x.ai/v1"
        else:
            base = "https://api.openai.com/v1"
    base = base.rstrip("/")
    model = os.environ.get("TUNDRA_LLM_MODEL") or (
        "grok-3" if "x.ai" in base else "gpt-4o-mini"
    )

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{base}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"]


def extract_yaml_block(text: str) -> str | None:
    """Pull first ```yaml ... ``` or ```tundra ... ``` fence."""
    m = re.search(r"```(?:yaml|tundra|yml)?\s*\n(.*?)```", text, re.S | re.I)
    if m:
        return m.group(1).strip() + "\n"
    if re.search(r"(?m)^tundra:\s*", text):
        m2 = re.search(r"(?ms)^(tundra:\s*.*?)(?=^## |\Z)", text)
        if m2:
            return m2.group(1).strip() + "\n"
    return None


def strip_yaml_fences(text: str) -> str:
    """Remove fenced YAML/tundra blocks so chat shows plain English only."""
    cleaned = YAML_FENCE.sub("", text)
    # Also drop a bare trailing tundra: document if model dumped without fences
    cleaned = re.sub(
        r"(?ms)^tundra:\s*.*",
        "",
        cleaned,
    )
    # Collapse excess blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def conversation_text(reply: str, yaml_text: str | None) -> str:
    """Text stored in the chat bubble (no YAML wall)."""
    say = strip_yaml_fences(reply)
    if say:
        return say
    if yaml_text:
        return (
            "I've updated the model draft on the right from your description. "
            "Please review it there.\n\n"
            "What other questions do you have?"
        )
    return reply.strip() or "I didn't catch a model update — could you say more?"


def has_api_key() -> bool:
    return bool(os.environ.get("XAI_API_KEY") or os.environ.get("OPENAI_API_KEY"))
