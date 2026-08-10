# Examples

Each subfolder is one complete Tundra example. The `.tundra` file in that folder is the **canonical model** (there is no separate `models/` tree).

| Folder | Domain | Illustrates | Code |
|--------|--------|-------------|------|
| [consultant-hours](consultant-hours/) | Hours → client invoice | Core six concepts + Relationships | Python, C |
| [loan-application](loan-application/) | Credit decision (BankID, UC) | **Intentional bad model** — untestable Contracts; counter-example / prompt testing | Model only |
| [booking-reservation](booking-reservation/) | Guest / host booking | Temporal + capacity decorators | Elixir |
| [ecommerce-order](ecommerce-order/) | Cart and order lifecycle | Aggregational decorators, cancel windows | Model only |
| [marketplace-listing](marketplace-listing/) | Listing, offer, sale | Multi-party Relationships, expiry | Model only |
| [content-publish](content-publish/) | Editorial workflow | Writer / Editor / Reader, review expiry | Model only |
| [social-post](social-post/) | Posts and moderation | Short-form Relationships, privacy | Model only |

## How to use with prompts

1. Read [`../tundra.md`](../tundra.md) for the language definition.
2. Point extract / validate / implement at the relevant `examples/*/…​.tundra` files for style and naming consistency.
3. Prefer reusing Role and Relationship vocabulary from an example in the same domain over inventing near-synonyms.

## Adding a new example

1. Create `examples/<short-kebab-name>/`.
2. Add `<name>.tundra` following the format in `tundra.md`.
3. Add a short `README.md` (what it covers; how to run code if any).
4. Link it in the table above.
