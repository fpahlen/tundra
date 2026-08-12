# Changelog

## Unreleased

- **Interview extract (Package 2):** draft diffs after turn 1; pre-export checklist; `source: inferred`; split heuristic; prefer ids/`enforced_by`/`outcomes`/genesis
- Optional Contract **`source`** / **`rationale`** in schema
- **ecommerce-order** golden path with Contract ids + `enforced_by`
- Loan vague specimen moved to **`examples/bad-contracts/`** (excluded from `--all`; CI asserts vagueness warnings)
- CI: skill example body matches consultant-hours
- **`outcomes` / `when` / `otherwise`** for exclusive branches; same-subject multi-`results` is an error
- Interview session: recovery, ids, `enforced_by`, validation `outcomes`
- Reachability + smarter vagueness (comparative without digit)

## v1.5 (feature/simple-tundra-generator merged)

- **Active listening** = reframe intent as a draft `.tundra` YAML (not prose paraphrase)
- Close interview turns with open questions (“What other questions do you have?”), not closed yes/no
- Dogfood product model: `models/tundra-interview-session.tundra`
- **Checker hardening** (Lovable review): contract-quote match, requires/results vs states + genesis, subject-named states, no `System` under roles, coverage/timer/role warnings
- Spec: positioning vs Gherkin/BPMN/DbC; vocabulary collisions; `before` dual meaning; genesis requires
- `examples/bad-structure/` negative fixture; CI workflow; README MIT + venv

## v1.4.2

- Grok skill polish: frontmatter (Relationships, YAML, `models/`), tighter extract/validate/implement refs
- README: user-wide skill install via symlink

## v1.4.1

- **Usage convention:** in app projects, authoritative models live in **`models/*.tundra`** (flat)
- This methodology repo keeps demos under **`examples/`**
- Skill, prompts, README, and `tundra.md` document the two-context rule
- `tools/check_tundra.py --all` also discovers `models/` when present

## v1.4

- **YAML is the model format** (pretty style); `.tundra` files contain YAML
- JSON Schema: `schema/tundra.schema.json`
- Checker: `tools/check_tundra.py` (+ `requirements-dev.txt`)
- VS Code: `*.tundra` associated with YAML
- All examples + skill example converted; Process structure on every model
- Decorators as named YAML fields (`expires_in`, `before`, …)
- Scenario names use colons (`Happy path: …`)


## v1.3

- Language definition lives in **`tundra.md`**; root `README.md` is a thin entry map
- **Relationships** and **decorators** (temporal + aggregational) as first-class extensions
- Escape hatch (`guard:`) removed; Contracts stay plain English
- All models under **`examples/<name>/`** (no top-level `models/`)
- Common web-site examples: booking, ecommerce, marketplace, content-publish, social-post
- Prompts list full **Resources** (tundra.md, examples, sibling prompts)
- `loan-application` marked as intentional bad model for validator/prompt testing
- Grok skill paths updated for `examples/` + six concepts


## v1.2

- **Grok Build skill** at `.grok/skills/tundra/` (`/tundra` extract · validate · implement)
- Self-contained `references/` (format, prompts, example model) for user-wide install
- README: Use with Grok Build + optional `AGENTS.md` snippet

## v1.1.1

- Documented **scope and blindspots** (README + `docs/scope-and-blindspots.md`)
- Clarified that the five concepts target durable domain obligations, not every quality of long-running software

## v1.1

Promotable methodology pack.

### Format

- Processes gain light structure: **Actor**, **Requires**, **Results**
- Scenario vocabulary documented: `is broken` vs `is applied`
- README rewritten: pitch, why now, mapping to code, prompt pack index, roadmap

### Models

- `consultant-hours-invoice.tundra` upgraded (Process structure, Hours are Invoiced, extra error Scenario)
- `loan-application-entry.tundra` upgraded with Process structure; **vague Contracts kept on purpose** as a `validate-tundra` specimen
- Removed duplicate model under `examples/consultant-hours/`

### Examples

- Replaced happy-path-only demos with `demo.py` / `demo.c`
- Roles, per-subject state, correct Contract checks, three Scenarios

### Prompts

- extract / implement / validate aligned with light structure, Roles in code, and testability gates
