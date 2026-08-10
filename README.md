# Tundra

A plain-English language for specifying business processes with explicit roles, relationships, testable contracts, and executable scenarios.

**Tundra captures who may do what, under which conditions, and how you prove it** — so humans and AIs can share one model of the business without treating source code as the only source of truth.

As AI writes more of the code, durable knowledge must live *above* the code. Tundra is that layer: thin models, explicit obligations, and living examples that become tests.

**Language definition:** [`tundra.md`](tundra.md)

## Repository layout

| Path | What it is |
|------|------------|
| [`tundra.md`](tundra.md) | Language definition (concepts, format, decorators, rules) |
| [`examples/`](examples/) | All worked models — one subfolder per example |
| [`prompts/`](prompts/) | Standalone AI prompts: extract, validate, implement |
| [`.grok/skills/tundra/`](.grok/skills/tundra/) | Grok Build skill (`/tundra`) |
| [`docs/scope-and-blindspots.md`](docs/scope-and-blindspots.md) | What Tundra optimizes for — and what it leaves out |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |

## Quick start

1. Read [`tundra.md`](tundra.md).
2. Browse [`examples/README.md`](examples/README.md).
3. In Grok Build: `/tundra interview` (or use the prompts under `prompts/`).

## Use with Grok Build

```text
/tundra interview
/tundra validate examples/
/tundra implement examples/consultant-hours/consultant-hours-invoice.tundra python
```

Skill path: [`.grok/skills/tundra/`](.grok/skills/tundra/).  
To install user-wide: copy or symlink that folder into `~/.grok/skills/tundra`.

Optional snippet for a consumer app’s `AGENTS.md`:

```markdown
## Domain rules
- Authoritative business process rules live in `examples/**/*.tundra` (Tundra format; see tundra.md).
- Do not invent Roles/Contracts; run /tundra extract or ask the human.
- Prefer implementing Processes from existing .tundra files.
```

## Prompt pack

```text
Human intent  →  extract-tundra  →  .tundra model(s)
                      ↓
                validate-tundra  →  quality report
                      ↓
                implement-tundra →  code + scenario tests
```

| Prompt | Job |
|--------|-----|
| [`prompts/extract-tundra.md`](prompts/extract-tundra.md) | Turn messy description into a thin model (or ask questions) |
| [`prompts/validate-tundra.md`](prompts/validate-tundra.md) | Check testability, structure, coverage, consistency |
| [`prompts/implement-tundra.md`](prompts/implement-tundra.md) | Generate faithful code and tests |

Always treat [`tundra.md`](tundra.md) as the definition of Tundra when using the prompts.

## House examples

| Example | Purpose |
|---------|---------|
| [`examples/consultant-hours/`](examples/consultant-hours/) | Clean reference model + Python/C demos |
| [`examples/loan-application/`](examples/loan-application/) | **Intentional bad model** — vague Contracts for prompt/validator testing |
| [`examples/booking-reservation/`](examples/booking-reservation/) | Temporal/capacity decorators + Elixir |
| Other folders under `examples/` | Common web-site patterns (model only) |

## License

See [LICENSE](LICENSE).
