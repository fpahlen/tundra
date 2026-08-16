# Sample: DORA (partial)

**Status:** first worked sample of the regulation translation system — not hard-wired into Tundra core.  
**Coverage:** **partial** — not a complete mapping of Articles 5–6.

| Item | Detail |
| --- | --- |
| Instrument | Regulation (EU) 2022/2554 (Digital Operational Resilience Act) |
| ELI | <https://eur-lex.europa.eu/eli/reg/2022/2554/oj> |
| Edition pin | OJ L 333, 27.12.2022 |
| Working excerpts | [`sources/`](sources/) |

## Models

| File | Kind | Scope |
| --- | --- | --- |
| [`dora-ict-risk-governance.tundra`](dora-ict-risk-governance.tundra) | lifecycle (modelling choice) | **Partial** Art. 5–6: selected duties + illustrative framework lifecycle |
| [`dora-art-5-4-board-competence.tundra`](dora-art-5-4-board-competence.tundra) | `kind: obligations` | Art. 5(4) only — standing duty, no invented states |

### Paragraph coverage (approx., both models)

Run for a live report:

```bash
python3 tools/check_tundra.py --coverage examples/regulations/dora/
```

Typical result (will move as models grow):

| Article | Cited paragraphs (sample) | Often missing |
| --- | --- | --- |
| 5 | 1, 2, 4 | 3 |
| 5(2) points | (a), (d) | (b)–(c), (e)–(i) |
| 6 | 1, 2, 4, 5, 8, 10 | 3, 6, 7, 9 |

Do **not** treat this folder as “full DORA Art. 5–6 compliance mapping.”

## How we cite

| Field | Role |
| --- | --- |
| `article` + `paragraph` | Primary |
| `quote` | Optional; checker verifies against `sources/` when present |
| `page` | Optional; only with pinned edition |

```bash
python3 tools/check_tundra.py examples/regulations/dora/
```

## Implement (Tundra → assets)

Standing duties (e.g. Art. 5(4) board knowledge) become a **control pack**, not fake unit tests:

→ [`implement/`](implement/)
