# MiFID II working excerpts (sample)

Helpers for the sample translation only. Official EUR-Lex / OJ text is authoritative.

Each file starts with trust front-matter:

```html
<!-- tundra-source: id=MIFID_II instrument="…" source_url="…" retrieved="YYYY-MM-DD" sha256="…" -->
```

- `id` binds the excerpt to the model pin (no cross-instrument use)  
- `sha256` is of the **body after** the comment (`tools/verify_sources.py` / `--write` to stamp)  
- Editing the body without updating the hash fails verification  

This proves “this is the paste we translated,” not “this is the Official Journal” by itself.

| File | Content |
| --- | --- |
| [`art-25.md`](art-25.md) | Article 25 — Assessment of suitability and appropriateness and reporting to clients |

**Not included:** Commission Delegated Regulation (EU) 2017/565 (Level 2 operational detail, e.g. Art. 54 suitability reports). That is a separate instrument if modelled later.
