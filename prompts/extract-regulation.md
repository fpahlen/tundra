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
4. Every Contract has **`cite`** with `article`, **`paragraph` (required when the article is numbered)**, and a **required continuous `quote`** (verbatim from that span — **no ellipsis**). Include carve-outs (`other than microenterprises`, …) in the quote when the sentence has them. The checker can only verify what you quote.  
5. Prefer **`kind: obligations`** for pure continuous duties (no `states`/`processes`). Use lifecycle only when the instrument has one. Scenarios still required (compliance/breach).  
6. **No invented thresholds** or secondary rules not in the supplied text  
7. Prefer **split** models; **one Contract per independently testable failure** (avoid one Contract citing many paragraphs)  
8. Optional `translation_review: {status: unreviewed}` until a human confirms text vs quote

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
        quote: "continuous verbatim snippet from that paragraph"
    translation_review:
      status: unreviewed
# states/processes: only for kind: lifecycle
scenarios: […]
```

End with open questions only about **gaps in the supplied legal slice**, not about YAML cosmetics.
