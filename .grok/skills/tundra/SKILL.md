---
name: tundra
description: >
  Plain-English YAML regulation translation system and domain obligation language
  (Roles, Relationships, Contracts, States, Processes, Scenarios, regulation+cite).
  Use for /tundra, .tundra models, any regulation reframe, extract-regulation, validate,
  or implement without inventing legal or business requirements.
when-to-use: >
  /tundra, tundra model, .tundra, models/, YAML tundra, regulation, article,
  lawyerish, extract-regulation, validate-tundra, implement-tundra, contracts and cites,
  compliance obligations, who-must-do-what
argument-hint: "[extract|validate|implement] [focus or path]"
metadata:
  short-description: "Regulation translation — YAML .tundra extract / validate / implement"
  author: tundra
---

# Tundra skill

You help humans and AIs translate **lawyerish requirements** (any applicable regulation
or policy) into plain-English Tundra models — and keep domain obligations explicit.

The language is **instrument-agnostic**. Do not hard-code duties or roles from a sample law
unless the user supplied that text.

Self-contained references:

```
<skill_dir>/references/format.md
<skill_dir>/references/extract.md
<skill_dir>/references/validate.md
<skill_dir>/references/implement.md
<skill_dir>/references/example.tundra
```

When inside the Tundra methodology repo, also prefer `tundra.md`,
`prompts/extract-regulation.md`, and samples under `examples/regulations/` only as style.

---

## Modes

| Mode | Triggers | Reference |
| --- | --- | --- |
| **extract** | regulation text, article paste, “reframe this law…”, `extract` | `extract.md` + `prompts/extract-regulation.md` when present |
| **validate** | `validate`, quality check | `validate.md` |
| **implement** | `implement`, generate code/tests from model | `implement.md` |

---

## Where files live

| Kind | Location |
| --- | --- |
| Your translations | **`models/*.tundra`** |
| Working excerpts (optional) | **`sources/<instrument>/`** |
| House samples (methodology repo) | **`examples/regulations/<instrument>/`** |

---

## Shared rules

1. **Never invent** duties or thresholds not in the supplied text.  
2. **Contracts must be testable.**  
3. Regulatory models need `regulation:` + **`cite`** (`article` / `paragraph`) on Contracts.  
4. **`source: inferred`** = AI assumption; not a legal cite. In conversation say “assumed.”  
5. **Thin models** — one slice per file.  
6. **Tone:** plain English for compliance and builders.

---

## Mode: extract

1. Pin `regulation` from **user-supplied** instrument metadata.  
2. Reframe operative text as Contracts with **`cite`**.  
3. Save under `models/<short-name>.tundra` (or path the user names).  
4. Offer validate next.

---

## Mode: validate / implement

Prefer `models/**/*.tundra`. Implement faithfully; keep provenance if the stack allows.

## Quick examples

```text
/tundra extract Article 5 from the regulation text I paste
/tundra validate models/
/tundra implement models/my-slice.tundra
```
