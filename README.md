# Tundra

A **regulation translation system**: plain-English middle language for obligations that humans and AIs can share — and a path from those obligations to **control packs and (where appropriate) code**.

Lawyerish regulatory text is already “the requirements.” Tundra reframes **any** applicable instrument into Roles, Contracts, States, Processes, and Scenarios with **legal provenance** (`regulation` + `cite`), then classifies how each duty is realized (`implement_as` / `evidence`).

The **core language is instrument-agnostic**. Specific laws appear only as **samples**.

**Language definition:** [`tundra.md`](tundra.md)  
**Model format:** YAML in `.tundra` files · [`schema/tundra.schema.json`](schema/tundra.schema.json)  
**License:** [MIT](LICENSE)

## What you get (the product surface)

For a standing duty such as DORA Art. 5(4) (board ICT knowledge) or MiFID II Art. 25(2) (suitability information), implement does **not** invent fake unit tests of competence or “product is suitable.” It produces a **control pack**:

| Asset | Example |
| --- | --- |
| Control statement + legal cite | [DORA Art. 5(4)](examples/regulations/dora/implement/art-5-4-control-pack.md) · [MiFID II Art. 25(2)](examples/regulations/mifid-ii-suitability/implement/art-25-2-control-pack.md) |
| Evidence design | training records, questionnaires, registers, attestation |
| Assurance probe | Scenario as internal-audit script |
| Machine-readable row | [art-5-4-controls.json](examples/regulations/dora/implement/art-5-4-controls.json) · [art-25-2-controls.json](examples/regulations/mifid-ii-suitability/implement/art-25-2-controls.json) |

**Drafting aids vs assurance:** the checker, coverage %, and excerpt `sha256` help you **draft and detect repo drift**. They do **not** prove the excerpt is the Official Journal, or that the firm complies. Evidence and human review do.

## Repository layout

| Path | What it is |
| --- | --- |
| [`tundra.md`](tundra.md) | Language definition (core) |
| [`schema/`](schema/) | JSON Schema (core) |
| [`tools/check_tundra.py`](tools/check_tundra.py) | Structural + provenance + fidelity checker |
| [`prompts/`](prompts/) | extract-regulation / validate / implement |
| [`models/`](models/) | Your translations |
| [`examples/regulations/`](examples/regulations/) | Sample translations + **implement/** control packs |
| [`archive/legacy-process/`](archive/legacy-process/) | Archived process-interview path |
| [`CHANGELOG.md`](CHANGELOG.md) | History |

## Quick start

1. Skim **What you get** above and the implement samples under [`examples/regulations/`](examples/regulations/) (DORA + MiFID II suitability).
2. Read [`tundra.md`](tundra.md) (regulatory models + implementation mapping).
3. Check samples:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements-dev.txt
   python tools/check_tundra.py --all
   python tools/check_tundra.py --coverage examples/regulations/dora/
   python tools/check_tundra.py --coverage examples/regulations/mifid-ii-suitability/
   python tools/verify_sources.py   # excerpt body hash = drift detection only
   ```

4. Translate: [`prompts/extract-regulation.md`](prompts/extract-regulation.md).
5. Implement: [`prompts/implement-tundra.md`](prompts/implement-tundra.md) — **code** for process guards, **control packs** for standing duties.

## Provenance (short)

```yaml
regulation:
  id: <INSTRUMENT_SHORT_ID>
  instrument: "<full legal name>"
  eli: "<stable official URL>"
  edition: "<pinned edition if using page>"

contracts:
  - id: example-duty
    text: Plain-English obligation…
    implement_as: capability   # or runtime_guard | recorded_control | governance | …
    evidence:
      - type: training_record
        description: …
    cite:
      - article: "<n>"
        paragraph: "<n>"
        quote: "continuous verbatim snippet"
```

Article + paragraph + quote are required for regulatory cites when excerpts exist. Excerpt `sha256` detects **local paste drift**, not Official Journal authenticity.

## Adding another regulation

1. Create `examples/regulations/<short-id>/` (sample) or put production work in your app’s `models/`.
2. Add thin `.tundra` files with `regulation:` + `cite` — **no core code changes**.

## Pivot note

Earlier process-interview work lives under [`archive/legacy-process/`](archive/legacy-process/). Active focus is regulation translation → controls (and code where it honestly applies).
