# Examples

Each subfolder is one complete Tundra **demo**. The `.tundra` file in that folder is the canonical example model (YAML).

In application projects, put product domain models under **`models/*.tundra`** (flat) — not here. See [`../README.md`](../README.md#where-to-put-models-in-your-project).

Structural schema: [`../schema/tundra.schema.json`](../schema/tundra.schema.json)  
Checker: `python3 tools/check_tundra.py --all` (from repo root; see [`../requirements-dev.txt`](../requirements-dev.txt))

| Folder | Domain | Illustrates | Code |
| --- | --- | --- | --- |
| [consultant-hours](consultant-hours/) | Hours → client invoice | Core six concepts + Relationships | Python, C |
| [loan-application](loan-application/) | Credit decision (BankID, UC) | **Intentional bad model** — untestable Contracts; counter-example / prompt testing | Model only |
| [booking-reservation](booking-reservation/) | Guest / host booking | Temporal + capacity decorators | Elixir |
| [ecommerce-order](ecommerce-order/) | Cart and order lifecycle | Aggregational decorators, cancel windows | Model only |
| [marketplace-listing](marketplace-listing/) | Listing, offer, sale | Multi-party Relationships, expiry | Model only |
| [content-publish](content-publish/) | Editorial workflow | Writer / Editor / Reader, review expiry | Model only |
| [social-post](social-post/) | Posts and moderation | Short-form Relationships, privacy | Model only |
| [bad-structure](bad-structure/) | Checker regression | **Intentional FAIL** for `check_tundra.py` (not a style reference) | Fixture only |

## How to use with prompts

1. Read [`../tundra.md`](../tundra.md) for the language definition (YAML).
2. Point extract / validate / implement at the relevant `examples/*/*.tundra` files for style and naming consistency.
3. Prefer reusing Role and Relationship vocabulary from an example in the same domain over inventing near-synonyms.

## Adding a new example

1. Create `examples/<short-kebab-name>/`.
2. Add `<name>.tundra` as **YAML** following [`../tundra.md`](../tundra.md).
3. Run `python3 tools/check_tundra.py examples/<short-kebab-name>/`.
4. Add a short `README.md` and link it in the table above.
