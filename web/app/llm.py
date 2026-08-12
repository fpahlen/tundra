"""LLM client (OpenAI-compatible) + demo facilitator."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

from app.paths import EXTRACT_PROMPT, FORMAT_MD, TUNDRA_MD


def load_system_prompt() -> str:
    parts = [
        EXTRACT_PROMPT.read_text(encoding="utf-8"),
        "\n\n---\n# tundra.md (language definition)\n\n",
    ]
    if TUNDRA_MD.is_file():
        parts.append(TUNDRA_MD.read_text(encoding="utf-8"))
    elif FORMAT_MD.is_file():
        parts.append(FORMAT_MD.read_text(encoding="utf-8"))
    parts.append(
        "\n\n---\nYou are the Facilitator in a web interview. "
        "On turn 1 emit a full draft .tundra YAML in a ```yaml fenced block. "
        "On later turns lead with a ## Changes diff, then the full updated YAML "
        "in a fenced block, then Gaps and an open question. "
        "Never invent measurable thresholds. Prefer Contract ids and enforced_by.\n"
    )
    return "".join(parts)


def demo_reply(user_message: str, turn: int, prior_yaml: str | None) -> str:
    """Deterministic facilitator when no API key is set."""
    name = "Interview draft"
    # crude name from first line of user text
    first = user_message.strip().split("\n")[0][:60] or "business process"
    slug = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")[:40] or "process"

    draft = f"""tundra: {name} ({slug})

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
        return (
            "Here is a first Tundra reframe of what you described "
            "(demo mode — set XAI_API_KEY or OPENAI_API_KEY for a live model).\n\n"
            f"```yaml\n{draft.strip()}\n```\n\n"
            "## Gaps\n"
            "- Confirm Roles and whether `source: inferred` Contracts match your domain.\n"
            "- Add measurable thresholds if any decision branches exist.\n\n"
            "## Check\n"
            "What other questions do you have?\n"
        )

    return (
        "## Changes\n"
        f"- Incorporated your note: {user_message.strip()[:120]!r}\n"
        "- Kept structure; please confirm inferred Contracts.\n\n"
        f"```yaml\n{(prior_yaml or draft).strip()}\n```\n\n"
        "## Gaps\n"
        "- Still confirm any `source: inferred` items.\n\n"
        "## Check\n"
        "What did I get wrong or leave out?\n"
    )


async def chat_completion(messages: list[dict[str, str]]) -> str:
    """Call OpenAI-compatible Chat Completions API."""
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Caller should use demo_reply instead
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
    # bare document starting with tundra:
    if re.search(r"(?m)^tundra:\s*", text):
        # take from first tundra: to end or next ##
        m2 = re.search(r"(?ms)^(tundra:\s*.*?)(?=^## |\Z)", text)
        if m2:
            return m2.group(1).strip() + "\n"
    return None


def has_api_key() -> bool:
    return bool(os.environ.get("XAI_API_KEY") or os.environ.get("OPENAI_API_KEY"))
