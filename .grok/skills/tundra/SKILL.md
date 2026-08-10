---
name: tundra
description: >
  Plain-English business rules for vibe coding (Roles, Contracts, States,
  Processes, Scenarios). Use when the user wants /tundra, domain rules,
  who-may-do-what, extract or interview a .tundra model, validate models,
  implement from Tundra, or keep AI from inventing business requirements.
when-to-use: >
  /tundra, tundra model, .tundra, extract-tundra, validate-tundra,
  implement-tundra, business process rules, contracts and roles for a feature
argument-hint: "[extract|interview|validate|implement] [focus or path]"
metadata:
  short-description: "Rails under the vibes — .tundra extract / validate / implement"
  author: tundra
---

# Tundra skill

You help humans and AIs keep **who may do what** explicit while vibe coding.

Self-contained references live next to this file:

```
<skill_dir>/references/format.md
<skill_dir>/references/extract.md
<skill_dir>/references/validate.md
<skill_dir>/references/implement.md
<skill_dir>/references/example.tundra
```

Resolve `<skill_dir>` as the directory containing this `SKILL.md` (from system context).  
**Always `read_file` `references/format.md` first** in a run. Then read the mode file you need.  
Use `references/example.tundra` as the clean few-shot shape when helpful.

---

## Modes

Infer mode from the user message / slash args. Default: **extract** (interview).

| Mode | Triggers | Reference |
|------|----------|-----------|
| **extract** / **interview** | messy feature talk, “model this”, no mode, `extract`, `interview` | `extract.md` |
| **validate** | `validate`, quality check, “is this model ok” | `validate.md` |
| **implement** | `implement`, “generate code from …”, language named | `implement.md` |

If the user only says `/tundra` with no focus, briefly explain the three modes and ask what they want to model (one short question). Stay light.

---

## Shared rules (all modes)

1. **Never invent** important Roles, Relationships, Contracts, States, or Processes. Ask instead.  
2. **Contracts must be testable** — refuse vagueness (“too high”, “reasonable”, “low risk”, “falls between”).  
3. **Thin models** — one focused concern per file.  
4. **Tone:** collaborative, plain language, short. Non-coders should understand model text.  
5. Do **not** lecture on blindspots unless the user asks or a gap blocks the task.  
6. Prefer writing files under `examples/<short-name>/` when this repo is the project; otherwise ask where to put `.tundra` files (suggest a focused folder, not a dump into root).  
7. After **extract**, offer **validate**. After validate **Ready**, offer **implement**. Do not force the whole loop.

---

## Mode: extract / interview

1. Read `format.md` + `extract.md`.  
2. If existing `*.tundra` files are in the project, list/read them for Role/Contract consistency.  
3. From the user’s description, either:  
   - ask **few** clarifying questions (missing actors, vague thresholds, unclear subject), or  
   - write a complete `.tundra` model in the exact format.  
4. Save to e.g. `examples/<short-name>/<short-name>.tundra` when working in this repo; otherwise a path the human chooses.  
5. Show a short summary (Roles + Contracts count + Scenario names), not a wall of theory.  
6. Ask if they want validate next.

**Interview style:** one clear question at a time when blocked; otherwise ship a thin model quickly so they can react.

---

## Mode: validate

1. Read `format.md` + `validate.md`.  
2. Targets: paths the user named, or all `**/*.tundra` / `examples/**/*.tundra` in the project.  
3. Produce the validation report structure from `validate.md`.  
4. Be direct. House models may be deliberate specimens (e.g. intentional vague Contracts) — still report findings; note if the README marks a specimen.  
5. Ask if they want help fixing issues or implementing a Ready model.

---

## Mode: implement

1. Read `format.md` + `implement.md`.  
2. Require a concrete `.tundra` path (or the model just extracted).  
3. Target language: user-specified, else match the project, else ask (Python is a fine default for demos).  
4. Implement faithfully: Roles as actors, state **per subject**, Contract fail-fast with Contract text, **all** Scenarios as tests.  
5. Do not invent rules. If the model is too vague, stop and suggest validate/fix first.  
6. Respect existing project layout and conventions when present.

---

## Quick examples (for you, not to dump on the user)

```text
/tundra interview consultant submits hours, manager invoices, client approves
/tundra validate models/
/tundra implement models/consultant-hours-invoice.tundra python
```

---

## Out of scope for this skill

Architecture diagrams, performance SLOs, deep security reviews, full UX copy — say so briefly and stay on Tundra.  
For philosophy and blindspots, point at the project `README.md` / `docs/scope-and-blindspots.md` when the user is inside the Tundra repo; do not require those files when the skill is installed user-wide (format.md is enough).
