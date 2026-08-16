# extract-regulation

You reframe **regulatory / lawyerish text** into a thin Tundra model humans and AIs can reason about.

This path is **instrument-agnostic**: any regulation, directive, standard, or policy text the user supplies.  
Sibling: `prompts/validate-tundra.md`, language: `tundra.md`.

---

## Resources

1. **`tundra.md`** — language definition (six concepts, `regulation`, `cite`)
2. **`schema/tundra.schema.json`** — structure
3. Official instrument text — **authoritative**
4. Optional working excerpts the user provides under `sources/<instrument>/`
5. Existing thin models under **`models/`** — style only; do not assume a particular law
6. Optional house samples under **`examples/regulations/`** — examples, not defaults to copy blindly

---

## Input

- One instrument pin (short id, full name, stable URL, edition when known)
- One or more articles / paragraphs (or excerpt paths)
- Optional: “amend” an existing `.tundra` model

---

## What you must produce

A complete `.tundra` YAML document:

1. **`regulation:`** block with `id`, `instrument`, and `eli` (or equivalent URL) when known; `edition` when pages are used  
2. **Roles / Relationships** named as in **this** text  
3. **Contracts** — plain English, testable; prefer `id` + `text`  
4. Every Contract has **`cite`** with at least `article` (and `paragraph` when the text has one); optional short `quote`  
5. Light **States / Processes / Scenarios** when the slice has a lifecycle; do not invent a fake process for pure continuous duties unless it helps builders  
6. **No invented thresholds** or secondary rules not in the supplied text  
7. Prefer **split** models over one fat file  

### Chat / explanation tone (if any)

- Prove you understood the **obligations**, not the tooling  
- Say “assumed” only if you marked `source: inferred` in YAML  
- Legal provenance is **`cite`**, never `source: inferred`

---

## Cite rules

| Prefer | Avoid |
| --- | --- |
| `article` + `paragraph` | Page-only cites without `regulation.edition` |
| One Contract ≈ one clear duty | Merging unrelated paragraphs into one Contract |
| Short `quote` when the paragraph is long | Full article dump inside `quote` |
| Names and structure from **this** instrument | Hard-coding roles or duties from another law |

---

## Output shape

```yaml
tundra: <instrument-slice-kebab>

regulation:
  id: <INSTRUMENT_SHORT_ID>
  instrument: "<full legal name>"
  eli: "<stable official URL>"
  edition: "<pinned edition if known>"

roles: […]
relationships: […]
contracts:
  - id: …
    text: …
    cite:
      - article: "<n>"
        paragraph: "<n>"
states: […]
processes: […]
scenarios: […]
```

End with open questions only about **gaps in the supplied legal slice**, not about YAML cosmetics.
