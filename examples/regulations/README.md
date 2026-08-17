# Regulation translation samples

These folders are **worked examples** of translating a legal instrument into Tundra.  
They are **not** part of the language core (`tundra.md`, schema, checker).

| Instrument | Path |
| --- | --- |
| DORA (EU) 2022/2554 — first sample (ICT governance) | [`dora/`](dora/) |
| MiFID II 2014/65/EU Art. 25 — suitability / appropriateness | [`mifid-ii-suitability/`](mifid-ii-suitability/) |

Add another regulation by creating `examples/regulations/<short-id>/` with:

- a pin + working excerpts under `sources/` (optional)
- one or more thin `.tundra` translation files

Core code and docs stay instrument-agnostic: no new checker rules per regulation.
