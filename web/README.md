# Tundra Interview (web)

Stage 1 of the simple Tundra file generator: **interview → reframe as `.tundra` → validate → export**.

Aligns with `models/tundra-interview-session.tundra` (Author / Facilitator / System).

## Run

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Demo mode (no AI key)

```bash
uvicorn app.main:app --reload --app-dir . --port 8001
```

Header badge shows **LLM: demo**.

### Live AI (xAI / Grok)

1. Copy the example env file and add your key (**never commit `.env`**):

```bash
cp .env.example .env
# edit .env — set XAI_API_KEY=...
```

2. Start the server (loads `web/.env` automatically via `python-dotenv`):

```bash
uvicorn app.main:app --reload --app-dir . --port 8001
```

3. Confirm the header badge shows **LLM: live**.

| Variable | Purpose |
| --- | --- |
| `XAI_API_KEY` | Preferred — xAI Grok (OpenAI-compatible API) |
| `OPENAI_API_KEY` | Alternative provider |
| `TUNDRA_LLM_BASE_URL` | Override API base (default `https://api.x.ai/v1` when using xAI) |
| `TUNDRA_LLM_MODEL` | Override model (default `grok-3` for xAI) |

You can also `export XAI_API_KEY=...` in the shell instead of a file.

### Secrets and GitHub

- **Do** put real keys only in `web/.env` or the process environment.
- **Do not** commit `.env`, paste keys into issues, or log them.
- Root [`.gitignore`](../.gitignore) already ignores `.env` and `.env.*`, and allows `.env.example`.
- For production, use the host’s secret store (not a checked-in file).

Open http://127.0.0.1:8001 (or whatever port you chose).

## What it does

| Feature | Behaviour |
| --- | --- |
| **Conversation (left)** | Plain English only — human dialogue about what the model means |
| **Model draft (right)** | Full `.tundra` YAML extracted from a fenced block in the LLM reply |
| Auto-validate | After each draft, runs `tools/check_tundra.py` rules |
| Checklist | Pre-export gates (structural, genesis, inferred, vagueness, …) |
| Export | Download `.tundra` only when checklist **blocking** items pass |
| Demo mode | No API key → deterministic sample reframe |

The Facilitator still produces YAML (for the right panel), but chat **strips** fenced YAML so the conversation does not dump the whole file.

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
