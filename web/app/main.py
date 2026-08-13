"""FastAPI app: Tundra interview stage 1."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.llm import (
    chat_completion,
    conversation_text,
    demo_reply,
    extract_yaml_block,
    has_api_key,
    load_system_prompt,
)
from app.paths import REPO_ROOT, WEB_ROOT
from app.sessions import Message, store
from app.snapshot import LAST_PATH, write_snapshot
from app.validate import validate_tundra_yaml

# Load secrets from local .env only (never commit .env — see .gitignore)
load_dotenv(WEB_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env")

STATIC = Path(__file__).resolve().parents[1] / "static"

app = FastAPI(title="Tundra Interview", version="0.1.0")


class ChatIn(BaseModel):
    message: str = Field(min_length=1)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "llm": "live" if has_api_key() else "demo",
    }


@app.post("/api/sessions")
def create_session() -> dict:
    s = store.create()
    write_snapshot(s)
    return s.public()


@app.get("/api/sessions")
def list_sessions() -> dict:
    """Dev helper: list in-memory session ids (newest last)."""
    return {"sessions": store.list_ids(), "last": store.last_id()}


@app.get("/api/sessions/{sid}")
def get_session(sid: str) -> dict:
    s = store.get(sid)
    if not s:
        raise HTTPException(404, "session not found")
    return s.public()


@app.get("/api/sessions/{sid}/snapshot")
def session_snapshot(sid: str) -> Response:
    """Markdown dump for agents: conversation + draft + checklist + validation."""
    s = store.get(sid)
    if not s:
        raise HTTPException(404, "session not found")
    path = write_snapshot(s)
    return Response(
        path.read_text(encoding="utf-8"),
        media_type="text/markdown; charset=utf-8",
    )


@app.get("/api/debug/last")
def debug_last() -> Response:
    """Latest auto-written snapshot (same as web/debug/last-session.md)."""
    if not LAST_PATH.is_file():
        raise HTTPException(
            404,
            "no snapshot yet — use the interview UI or POST /api/sessions first",
        )
    return Response(
        LAST_PATH.read_text(encoding="utf-8"),
        media_type="text/markdown; charset=utf-8",
    )


@app.post("/api/sessions/{sid}/chat")
async def chat(sid: str, body: ChatIn) -> dict:
    s = store.get(sid)
    if not s:
        raise HTTPException(404, "session not found")
    if s.session_state == "Abandoned":
        raise HTTPException(400, "session abandoned")

    s.messages.append(Message(role="author", content=body.message.strip()))
    s.turn += 1
    s.session_state = "Open"

    if has_api_key():
        system = load_system_prompt()
        history: list[dict[str, str]] = [{"role": "system", "content": system}]
        # Chat history is plain English only; inject current draft so the model can revise it
        if s.draft_yaml:
            history.append(
                {
                    "role": "system",
                    "content": (
                        "Current model draft on the right-hand panel "
                        "(revise this YAML in your fenced block):\n\n"
                        f"```yaml\n{s.draft_yaml.strip()}\n```"
                    ),
                }
            )
        for m in s.messages:
            if m.role == "system":
                continue
            role = "assistant" if m.role == "facilitator" else "user"
            history.append({"role": role, "content": m.content})
        try:
            reply = await chat_completion(history)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"LLM error: {exc}") from exc
    else:
        reply = demo_reply(body.message, s.turn, s.draft_yaml)

    yaml_text = extract_yaml_block(reply)
    # Conversation bubble: plain English only (YAML goes to the draft panel)
    s.messages.append(
        Message(role="facilitator", content=conversation_text(reply, yaml_text))
    )

    if yaml_text:
        s.draft_yaml = yaml_text
        s.draft_state = "Proposed"
        report = validate_tundra_yaml(yaml_text)
        s.last_validation = report
        if report["ok"]:
            s.draft_state = "Structurally valid"
        else:
            s.draft_state = "Structurally invalid"

    s.session_state = "Awaiting Author input"
    write_snapshot(s)
    return s.public()


@app.post("/api/sessions/{sid}/validate")
def validate(sid: str) -> dict:
    s = store.get(sid)
    if not s:
        raise HTTPException(404, "session not found")
    if not s.draft_yaml:
        raise HTTPException(400, "no draft yet")
    report = validate_tundra_yaml(s.draft_yaml)
    s.last_validation = report
    if report["ok"]:
        s.draft_state = "Structurally valid"
    else:
        s.draft_state = "Structurally invalid"
    write_snapshot(s)
    return {"session": s.public(), "report": report}


@app.post("/api/sessions/{sid}/export")
def export(sid: str) -> PlainTextResponse:
    s = store.get(sid)
    if not s:
        raise HTTPException(404, "session not found")
    if not s.export_allowed():
        raise HTTPException(
            400,
            "export not allowed: need structural OK and pre-export checklist clear "
            "(confirm inferred Contracts, fix vagueness, genesis, etc.)",
        )
    assert s.draft_yaml
    s.draft_state = "Exported"
    write_snapshot(s)
    filename = "model.tundra"
    # try tundra: name
    for line in s.draft_yaml.splitlines():
        if line.startswith("tundra:"):
            raw = line.split(":", 1)[1].strip().lower()
            safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in raw)
            safe = "-".join(p for p in safe.split("-") if p)[:48]
            if safe:
                filename = f"{safe}.tundra"
            break
    return PlainTextResponse(
        s.draft_yaml,
        media_type="text/yaml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/sessions/{sid}/abandon")
def abandon(sid: str) -> dict:
    s = store.abandon(sid)
    if not s:
        raise HTTPException(404, "session not found")
    write_snapshot(s)
    return s.public()


# Static assets last so /api wins
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
