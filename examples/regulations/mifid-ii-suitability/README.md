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

| Article | Cited paragraphs (sample) | Often missing / out of scope here |
| --- | --- | --- |
| 25 | 1–6 | 7 (mortgage-bond carve-out), 8–11 (delegated acts / ESMA guidelines mandates) |

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
