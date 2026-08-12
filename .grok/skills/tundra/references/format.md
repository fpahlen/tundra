# Tundra format (skill reference)

Plain-English models for **who may do what**, under which conditions, with living examples.

**Files:** suffix `.tundra`, content is **YAML**.  
**In apps:** store under `models/*.tundra` (flat).  
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

roles:
  - <Role name>

relationships:
  - <Role> is <Relationship> of <subject>

contracts:
  - <testable rule>

states:
  - <Subject is Some state>
  - name: <Subject is Some state>
    expires_in: 15 minutes

processes:
  - name: <Process name>
    actor: <Role or System>
    requires: <State or short condition>
    results: <State or short outcome>

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
      - And the contract "..." is broken

```

## Scenario vocabulary

| Situation | Phrase |
| --- | --- |
| Forbidden action | `is broken` |
| Automatic rule fires correctly | `is applied` |

## Key rules

1. Never invent important knowledge — ask instead.  
2. Prefer thin models.  
3. Contracts must be testable.  
4. Roles and Relationships are first-class.  
5. Every State names its subject.  
6. Processes declare name, actor, requires, results.  
   - `actor: System` is allowed; do **not** list `System` under `roles:`.  
   - `requires` must be a declared State or a genesis condition (`nothing` / `no X exists`).  
7. Scenarios demonstrate Contracts; quoted contract text must match `contracts:` exactly.  
8. Output valid YAML only (shape in this file / `tundra.md`).

## Map to code

| Tundra | Code |
| --- | --- |
| Role | Actor param / enum |
| Relationship | Ownership / association checks |
| Contract | Fail-fast; message quotes Contract text |
| State | Enum **per subject** |
| Process | One function; guard actor + requires |
| Scenario | Executable test |
