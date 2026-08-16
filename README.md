# Tundra

A **regulation translation system**: plain-English middle language for obligations that humans and AIs can share.

Lawyerish regulatory text is already “the requirements.” Tundra reframes **any** applicable instrument into Roles, Contracts, States, Processes, and Scenarios with **legal provenance** (`regulation` + `cite` → article / paragraph) so compliance and builders work from one map.

The **core language is instrument-agnostic**. Specific laws appear only as **samples**.

**Language definition:** [`tundra.md`](tundra.md)  
**Model format:** YAML in `.tundra` files · [`schema/tundra.schema.json`](schema/tundra.schema.json)  
**License:** [MIT](LICENSE)

## Repository layout

| Path | What it is |
| --- | --- |
| [`tundra.md`](tundra.md) | Language definition (core) |
| [`schema/`](schema/) | JSON Schema (core) |
| [`tools/check_tundra.py`](tools/check_tundra.py) | Structural + provenance checker (core) |
| [`prompts/`](prompts/) | Generic extract / validate / implement |
| [`models/`](models/) | Your translations |
| [`examples/regulations/`](examples/regulations/) | Sample translations of real instruments |
| [`archive/legacy-process/`](archive/legacy-process/) | Archived process-interview path |
| [`CHANGELOG.md`](CHANGELOG.md) | History |

## Quick start

1. Read [`tundra.md`](tundra.md) (especially **Regulatory models**).
2. Optionally browse a sample under [`examples/regulations/`](examples/regulations/).
3. Check models:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements-dev.txt
   python tools/check_tundra.py --all
   ```

4. Translate further articles with [`prompts/extract-regulation.md`](prompts/extract-regulation.md) — pass **any** instrument text; the prompt is not tied to one law.
5. Implement with [`prompts/implement-tundra.md`](prompts/implement-tundra.md): **code** for process guards, **control packs** for standing duties (see [`examples/regulations/dora/implement/`](examples/regulations/dora/implement/)).

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
    cite:
      - article: "<n>"
        paragraph: "<n>"
```

Article + paragraph are primary. Pages are optional and only valid for a pinned edition.

## Adding another regulation

1. Create `examples/regulations/<short-id>/` (sample) or put production work in your app’s `models/`.
2. Add thin `.tundra` files with `regulation:` + `cite` — **no core code changes**.

## Pivot note

Earlier process-interview work lives under [`archive/legacy-process/`](archive/legacy-process/). Active focus is the regulation translation system.
