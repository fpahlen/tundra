# Tundra Interview (web)

Stage 1 of the simple Tundra file generator: **interview → reframe as `.tundra` → validate → export**.

Aligns with `models/tundra-interview-session.tundra` (Author / Facilitator / System).

## Run

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Demo facilitator (no API key) — UI fully usable
uvicorn app.main:app --reload --app-dir .

# Live LLM (OpenAI-compatible)
export XAI_API_KEY=...          # preferred for Grok
# or: export OPENAI_API_KEY=...
# optional:
# export TUNDRA_LLM_BASE_URL=https://api.x.ai/v1
# export TUNDRA_LLM_MODEL=grok-3

uvicorn app.main:app --reload --app-dir . --port 8000
```

Open http://127.0.0.1:8000

## What it does

| Feature | Behaviour |
| --- | --- |
| Chat | Author messages → Facilitator (extract prompt + `tundra.md`) |
| Draft | YAML block extracted; shown in right panel |
| Auto-validate | After each draft, runs `tools/check_tundra.py` rules |
| Checklist | Pre-export gates (structural, genesis, inferred, vagueness, …) |
| Export | Download `.tundra` only when checklist **blocking** items pass |
| Demo mode | No API key → deterministic sample reframe |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/sessions` | Start session |
| `GET` | `/api/sessions/{id}` | Session snapshot |
| `POST` | `/api/sessions/{id}/chat` | Author message |
| `POST` | `/api/sessions/{id}/validate` | Re-run structural check |
| `POST` | `/api/sessions/{id}/export` | Download model (if allowed) |
| `POST` | `/api/sessions/{id}/abandon` | Abandon session |

## Limits (v0)

- In-memory sessions (lost on restart)
- No auth / multi-user
- Domain-ready is approximated by checklist (not a separate “gaps” state machine in storage)
- Live LLM quality depends on the model and the extract prompt

## Domain model

See [`../models/tundra-interview-session.tundra`](../models/tundra-interview-session.tundra).
