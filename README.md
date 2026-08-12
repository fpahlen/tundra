# Tundra

A plain-English language for specifying business processes with explicit roles, relationships, testable contracts, and executable scenarios.

**Tundra captures who may do what, under which conditions, and how you prove it** — so humans and AIs can share one model of the business without treating source code as the only source of truth.

As AI writes more of the code, durable knowledge must live *above* the code. Tundra is that layer: thin models, explicit obligations, and living examples that become tests.

Unlike Gherkin alone, Tundra is not “examples with no model”: **Roles, Relationships, Contracts, States, and Processes** sit beside Scenarios in one file a non-programmer can challenge — then AI prompts turn that file into code and tests. See [positioning in `tundra.md`](tundra.md#not-gherkin-bpmn-or-classical-design-by-contract).

**Language definition:** [`tundra.md`](tundra.md)  
**Model format:** YAML in `.tundra` files · [`schema/tundra.schema.json`](schema/tundra.schema.json)  
**License:** [MIT](LICENSE)

## Repository layout

| Path | What it is |
| --- | --- |
| [`tundra.md`](tundra.md) | Language definition (concepts, YAML format, decorators, rules) |
| [`schema/tundra.schema.json`](schema/tundra.schema.json) | JSON Schema for models |
| [`tools/check_tundra.py`](tools/check_tundra.py) | Structural checker |
| [`examples/`](examples/) | All worked models — one subfolder per example |
| [`prompts/`](prompts/) | Standalone AI prompts: extract, validate, implement |
| [`.grok/skills/tundra/`](.grok/skills/tundra/) | Grok Build skill (`/tundra`) |
| [`docs/scope-and-blindspots.md`](docs/scope-and-blindspots.md) | Scope and blindspots |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |

## Quick start

1. Read [`tundra.md`](tundra.md).
2. Browse [`examples/README.md`](examples/README.md).
3. Check models:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   python -m pip install -r requirements-dev.txt
   python tools/check_tundra.py --all
   python examples/consultant-hours/demo.py
   ```

4. In Grok Build: `/tundra interview` (or use `prompts/`).

## Where to put models in *your* project

This repository keeps **demos** under [`examples/`](examples/).  
In an application you own, put authoritative domain models under **`models/`** (flat):

```text
your-app/
  models/                         # source of truth for business rules
    hours-invoice.tundra
    order-lifecycle.tundra
  src/                            # code that implements those rules
```

- Create `models/` if it does not exist  
- One thin model per file; kebab-case names  
- Reuse Role and Relationship names across files in `models/`  
- Check them with: `python3 tools/check_tundra.py models/` (if you vendor the checker)

Optional snippet for a consumer app’s `AGENTS.md`:

```markdown
## Domain rules
- Authoritative business process rules live in `models/*.tundra` (Tundra YAML).
- Do not invent Roles/Contracts; run /tundra extract or ask the human.
- Prefer implementing Processes from existing `models/*.tundra` files.
```

## Use with Grok Build

**In your app** (default):

```text
/tundra interview
/tundra validate models/
/tundra implement models/hours-invoice.tundra python
```

**In this methodology repo** (house demos):

```text
/tundra validate examples/
/tundra implement examples/consultant-hours/consultant-hours-invoice.tundra python
```

Skill path: [`.grok/skills/tundra/`](.grok/skills/tundra/).

**Install user-wide** (so `/tundra` works in any project):

```bash
# from this repo root — symlink stays up to date with git pulls
ln -sfn "$(pwd)/.grok/skills/tundra" ~/.grok/skills/tundra

# or copy once (won't track updates):
# cp -R .grok/skills/tundra ~/.grok/skills/tundra
```

Confirm the skill appears in Grok’s skill list / responds to `/tundra`.

## Prompt pack

```text
Human intent  →  extract-tundra  →  .tundra model (YAML)
                      ↓
                validate-tundra  →  quality report
                      ↓
                implement-tundra →  code + scenario tests

```

| Prompt | Job |
| --- | --- |
| [`prompts/extract-tundra.md`](prompts/extract-tundra.md) | Turn messy description into a thin YAML model |
| [`prompts/validate-tundra.md`](prompts/validate-tundra.md) | Check testability, structure, coverage |
| [`prompts/implement-tundra.md`](prompts/implement-tundra.md) | Generate faithful code and tests |

Always treat [`tundra.md`](tundra.md) as the definition of Tundra.

## Interview website (Stage 1)

Local web UI for the interview → validate → export loop:

See [`web/README.md`](web/README.md).

```bash
cd web && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
# open http://127.0.0.1:8000
```

## House examples

| Example | Purpose |
| --- | --- |
| [`examples/consultant-hours/`](examples/consultant-hours/) | Clean reference + Python/C demos |
| [`examples/bad-contracts/`](examples/bad-contracts/) | **Intentional bad Contracts** fixture (vagueness) |
| [`examples/booking-reservation/`](examples/booking-reservation/) | Temporal/capacity decorators + Elixir |
| Other folders under `examples/` | Common web-site patterns (model only) |
| [`models/tundra-interview-session.tundra`](models/tundra-interview-session.tundra) | Product domain model for the interview site |

## License

See [LICENSE](LICENSE).
