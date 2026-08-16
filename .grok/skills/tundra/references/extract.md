# extract-tundra (skill reference)

You reframe messy human or **regulatory** input into a thin Tundra model.  
Always follow `format.md` (or project `tundra.md` / `prompts/extract-regulation.md` if present).

## Flow (regulation)

```text
instrument pin + article text
  → draft .tundra with regulation: + cite on each Contract
  → open questions only about legal gaps
  → save models/<slice>.tundra
```

## Flow (domain / feature talk)

```text
turn 1: full draft .tundra reframe
later:  DIFF + open question
```

## Active listening

- **Do not** only paraphrase (“What I heard…”).
- **Do** rewrite as YAML `.tundra`.
- Prove process/obligation understanding; do not narrate tooling (ids, genesis, “testable file”).
- Close with an **open** question when interviewing a human.

## Authoring rules

1. Contract **`id` + `text`**; Processes list **`enforced_by: [ids]`** when useful.  
2. **Regulatory:** `regulation:` pin; every Contract has **`cite`** (`article` / `paragraph`).  
3. At least one **genesis** Process when there is a subject lifecycle.  
4. Exclusive decisions use **`outcomes`**.  
5. **`source: inferred`** only for AI assumptions (chat: say “assumed”); not for law.  
6. Never invent thresholds or RTS detail not in the supplied text.  
7. Thin models: split by chapter/article cluster when a second independent lifecycle appears.

Default save: `models/<short-name>.tundra`.

## Tone

Brief, precise. Compliance and builders both read the model.
