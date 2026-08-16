# Tundra format (skill reference)

Plain-English models for **who must / may do what**, under which conditions, with living examples — including **regulatory** reframes of any instrument with legal provenance.

**Files:** suffix `.tundra`, content is **YAML**.  
**In apps / this repo:** store under `models/*.tundra` (flat).  
When the full Tundra repo is available, prefer `tundra.md` and `schema/tundra.schema.json` over this condensed file.

## Six concepts

| Concept | Meaning |
| --- | --- |
| **Roles** | Named actors (a person can hold several) |
| **Relationships** | Named connections (“A is X of B”, or short form “Author of Post”) |
| **Contracts** | Authoritative, testable rules — single source of truth |
| **States** | Meaningful situations of a **named subject** |
| **Processes** | Maps with **name**, **actor**, **requires**, **results** |
| **Scenarios** | End-to-end examples → tests (`steps` list of Given/When/Then/And) |

## Decorators (optional fields)

| Field | On | Example |
| --- | --- | --- |
| `expires_in` | state | `expires_in: 15 minutes` |
| `capacity` | state | `capacity: 1` |
| `quantity` | state / process | `quantity: at least 1` |
| `contains` | state | `contains: LineItems` |
| `before` | process | `before: start time` |
| `after` | process | `after: end time` |
| `within` | process | `within: 24 hours before start` |

Do **not** embed executable code in the model.

## Exact output format

```yaml
tundra: <short name>

# kind: obligations   # standing duties; omit processes/states
# kind: lifecycle     # default when processes present

# Regulatory models — pin the instrument (any law):
# regulation:
#   id: <INSTRUMENT_SHORT_ID>
#   instrument: "<full legal name>"
#   eli: "<stable official URL>"
#   edition: "<pinned edition if using page>"

roles:
  - <Role name>

relationships:
  - <Role> is <Relationship> of <subject>

contracts:
  - <testable rule>
  - id: only-manager-creates-invoice
    text: Only the Manager may create an invoice
    # implement_as: runtime_guard  # or recorded_control | capability | governance | …
    # evidence:
    #   - type: training_record
    #     description: …
    # cite:                    # legal provenance (regulatory)
    #   - article: "5"
    #     paragraph: "2"

states:
  - <Subject is Some state>
  - name: <Subject is Some state>
    expires_in: 15 minutes

processes:
  - name: <Process name>
    actor: <Role or System>
    requires: <State or genesis condition>
    results: <State or short outcome>   # AND; exclusive with outcomes
    # outcomes:                            # XOR branches (when / otherwise)
    #   - when: …
    #     results: …
    enforced_by: [only-manager-creates-invoice]

scenarios:
  - name: "Happy path: …"
    steps:
      - Given ...
      - When the <Role> ...
      - Then ...
  - name: "Error: …"
    steps:
      - Given ...
      - When the <Role> tries to ...
      - Then ...
      - And the contract [only-manager-creates-invoice] is broken

```

## Scenario vocabulary

| Situation | Phrase |
| --- | --- |
| Forbidden action | `is broken` (quote text or `[id]`) |
| Automatic rule fires correctly | `is applied` |

## Regulatory provenance

| Field | Meaning |
| --- | --- |
| `kind` | `obligations` \| `lifecycle` |
| `regulation` | Model-level pin (id, instrument, eli, edition) |
| `cite` | On Contracts/Processes: `article` + `paragraph` (primary); optional `quote` / `page` |
| `source: inferred` | AI assumption — **not** a legal cite |

Checker verifies quotes/paragraphs against `sources/` excerpts when present.  
Few-shot regulatory example: `example-regulation.tundra` + `sources/art-01.md`.

## Key rules

1. Never invent important knowledge — ask instead.  
2. Prefer thin models (one regulatory slice per file).  
3. Contracts must be testable.  
4. Regulatory models: every Contract should have **`cite`** with `article`.  
5. Roles and Relationships are first-class.  
6. Every State names its subject.  
7. Processes declare name, actor, requires, results.  
   - `actor: System` is allowed; do **not** list `System` under `roles:`.  
   - `requires` must be a declared State or a genesis condition (`nothing` / `no X exists`).  
   - Prefer `enforced_by: [contract-id, …]` linking to Contract ids.  
8. Scenarios demonstrate Contracts; quotes must match text, or use `[id]`.  
9. Output valid YAML only (shape in this file / `tundra.md`).

## Map to code

| Tundra | Code |
| --- | --- |
| Role | Actor param / enum |
| Relationship | Ownership / association checks |
| Contract | Fail-fast; message quotes Contract text |
| `enforced_by` | Which Contracts to check in that Process function |
| State | Enum **per subject** |
| Process | One function; guard actor + requires + enforced_by |
| Scenario | Executable test |
