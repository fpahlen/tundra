# DORA working excerpts (sample)

Helpers for the sample translation only. Official EUR-Lex / OJ text is authoritative.

Each file starts with trust front-matter:

```html
<!-- tundra-source: id=DORA instrument="…" source_url="…" retrieved="YYYY-MM-DD" sha256="…" -->
```

- `id` binds the excerpt to the model pin (no cross-instrument use)  
- `sha256` is of the **body after** the comment (`tools/verify_sources.py` / `--write` to stamp)  
- Editing the body without updating the hash fails verification  

This proves “this is the paste we translated,” not “this is the Official Journal” by itself.

| File | Content |
| --- | --- |
| [`art-05.md`](art-05.md) | Article 5 — Governance and organisation |
| [`art-06.md`](art-06.md) | Article 6 — ICT risk management framework |
