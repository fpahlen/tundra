# Changelog

## Unreleased

### Regulatory pivot (active)

- **Mission:** instrument-agnostic **regulation translation system** (not hard-coded to one law)
- **`regulation`** + **`cite`** with **quote/paragraph resolution** against `sources/`
- Sources **bound to `regulation.id`** (no cross-instrument fallback); excerpt `tundra-source` front-matter
- Quotes matched **inside the cited paragraph/point span** (misattribution errors)
- **`kind: obligations`** — duties + scenarios only (states/processes forbidden); no genesis
- **`--coverage`** report for article/paragraph/point vs excerpts
- Provenance CI fixtures (bad-cite, wrong-paragraph, obligations-escape, cross-instrument); skill `example-regulation.tundra`
- Tools refactor: `model_checks.py` phases, shared span slicing, thinner `check_tundra.py`
- Excerpt **sha256/source_url/retrieved**; `verify_sources.py`; **required quotes**; no ellipsis in quotes
- Coverage counts **quoted** cites only; catch-all / cites-per-contract warnings
- `translation_review` + modality-mismatch warnings (denial + soft shall→should)
- Scope-qualifier omission warning; require `paragraph` when excerpts are numbered
- **Demonstrated vs quoted** coverage; regulatory role checks use Contract mention
- **Implement path:** `implement_as` + `evidence` on Contracts; dual assets (code vs control pack);
  sample `examples/regulations/dora/implement/` for board-knowledge capability duty
- Review 5 follow-through: Contract-vs-quote **scope** warn; evidence required for non-runtime
  classes; stricter **demonstrated** coverage; soft-modal false-positive fix; `implemented_at` /
  `applies_when`; noisy re-stamp (`--force`); README “What you get”
- Review 6: `applies_when` joins scope check (not off-switch); population-after-cue + widening;
  `evidence.type` enum; date coerce; collapsed warning counts; distinct When for demonstrated
- **`prompts/extract-regulation.md`** — lawyerish → Tundra + cite (any instrument)
- **Sample only:** `examples/regulations/dora/` (partial Art. 5–6 + pure 5(4) slice)
- **`models/`** reserved for user translations (no house instrument models)
- **Archive:** process interview app, business examples → `archive/legacy-process/`

### Earlier (archived path)

- Interview web app, Package 2 extract, `source`/`rationale`, `outcomes`, genesis checks (see `archive/legacy-process/`)

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
