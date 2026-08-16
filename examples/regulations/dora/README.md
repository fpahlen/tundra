# Sample: DORA

**Status:** first worked sample of the regulation translation system — not hard-wired into Tundra core.

| Item | Detail |
| --- | --- |
| Instrument | Regulation (EU) 2022/2554 (Digital Operational Resilience Act) |
| ELI | <https://eur-lex.europa.eu/eli/reg/2022/2554/oj> |
| Edition pin | OJ L 333, 27.12.2022 |
| Translation | [`dora-ict-risk-governance.tundra`](dora-ict-risk-governance.tundra) (Art. 5–6 slice) |
| Working excerpts | [`sources/`](sources/) |

## How we cite (same for any instrument)

| Field | Role |
| --- | --- |
| `article` + `paragraph` | Primary |
| `quote` | Optional disambiguation |
| `page` | Optional; only with pinned edition |

```bash
python3 tools/check_tundra.py examples/regulations/dora/
```
