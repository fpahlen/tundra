# Sample: MiFID II suitability (partial)

**Status:** second worked sample of the regulation translation system — not hard-wired into Tundra core.  
**Purpose:** show the same pipeline on a **client-conduct / suitability** instrument, not only DORA-shaped ICT governance.  
**Coverage:** **partial** — Article 25 slice only; not full MiFID II.

| Item | Detail |
| --- | --- |
| Instrument | Directive 2014/65/EU (MiFID II) |
| ELI | <https://eur-lex.europa.eu/eli/dir/2014/65/oj> |
| Edition pin | OJ L 173, 12.6.2014 |
| Working excerpts | [`sources/`](sources/) |

## Models

| File | Kind | Scope |
| --- | --- | --- |
| [`mifid-ii-art-25-suitability.tundra`](mifid-ii-art-25-suitability.tundra) | `kind: obligations` | Art. 25 duties: staff competence, suitability, appropriateness, execution-only gate, client agreement record, suitability statement |

### Why this instrument

| DORA sample | This sample |
| --- | --- |
| ICT risk, management body, frameworks | Client suitability / appropriateness |
| Board knowledge, control functions | Advisers, fact-find, warnings, statements |
| Entity-internal governance | Firm ↔ client conduct duties |

Core checkers stay instrument-agnostic; this folder only exercises them.

### Paragraph coverage (approx.)

```bash
python3 tools/check_tundra.py --coverage examples/regulations/mifid-ii-suitability/
```

| Article | Modelled | out_of_scope (denominator) |
| --- | --- | --- |
| 25 | duty-units under paras 1–6 (multi-subparagraph split where present) | 7 (mortgage cross-ref), 8 (Commission), 9–11 (ESMA) |

Coverage uses **duty-units** (paragraphs split on unnumbered subparagraphs) and reports **implementable (by design)** — not assurance.  
Do **not** treat this folder as “full MiFID II Art. 25 compliance mapping.”  
Level 2 (e.g. Delegated Regulation (EU) 2017/565 Art. 54) is **not** cited here — separate instrument if added later.

## How we cite

| Field | Role |
| --- | --- |
| `article` + `paragraph` | Primary |
| `quote` | Required continuous snippet; checker verifies against `sources/` |
| `page` | Optional; only with pinned edition |

```bash
python3 tools/check_tundra.py examples/regulations/mifid-ii-suitability/
python3 tools/verify_sources.py examples/regulations/mifid-ii-suitability/sources/
```

## Implement (Tundra → assets)

Suitability duties become a **control pack** (recorded controls + evidence), not fake “product is suitable” unit tests:

→ [`implement/`](implement/)
