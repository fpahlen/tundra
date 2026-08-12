# Tundra

A plain-English language for specifying business processes with explicit roles, relationships, testable contracts, and executable scenarios.

**Tundra captures who may do what, under which conditions, and how you prove it** — so humans and AIs can share one model of the business without treating source code as the only source of truth.

As AI writes more of the code, durable knowledge must live *above* the code. Tundra is that layer: thin models, explicit obligations, and living examples that become tests.

Models are deliberately thin.  
A whole system is normally made of many small models rather than one large model.

**Files use the suffix `.tundra` and contain YAML** (pretty style: English as leaf values, light structure for Processes and Scenarios).

## Examples (this repository)

Worked demos live under [`examples/`](examples/).  
See [`examples/README.md`](examples/README.md) for the full catalog.

## Where models live in *your* project

In an application, keep authoritative `.tundra` files under **`models/`**, flat by default:

```text
models/
  hours-invoice.tundra
  order-lifecycle.tundra
```

Do not scatter product rules under `examples/` — that folder is for demos.  
Create `models/` if needed; one thin model per file; kebab-case names.

**Schema & check:** [`schema/tundra.schema.json`](schema/tundra.schema.json) · [`tools/check_tundra.py`](tools/check_tundra.py)

```bash
python3 -m pip install -r requirements-dev.txt
python3 tools/check_tundra.py --all          # this repo: examples + skill sample
python3 tools/check_tundra.py models/        # your app
```

---

## Why Tundra?

Most teams either bury rules in code (invisible to non-programmers) or scatter them across tickets and wikis (invisible to machines). Tundra sits in between:

| Audience | What they get |
| --- | --- |
| Humans | Plain language they can read, challenge, and change |
| AIs | Structure disciplined enough to extract, validate, and implement without inventing rules |
| Both | A common language for *good* software: explicit knowledge, single source of truth, design by contract |

### Not Gherkin, BPMN, or classical Design by Contract

| Neighbour | Overlap | What Tundra adds |
| --- | --- | --- |
| Gherkin / Cucumber | Scenario steps look like Given/When/Then | A **model** behind the examples: Roles, Relationships, Contracts, States, Processes — scenarios are evidence, not the whole spec |
| BPMN / workflow tools | States + Processes | Diffable text, plain-language obligations (Contracts), no proprietary diagram lock-in |
| Design by Contract in code | `requires` / `results` | Obligations lifted **above** code, editable by non-programmers |
| Statecharts alone | Lifecycle | First-class **who may act** (Roles) and **why** (Contracts) |

Tundra is for durable **domain obligations** living next to (not inside) implementation.

### Vocabulary collisions

In UML, BPMN, classical DbC, and the actor model, the words **Actor**, **Process**, **Contract**, and **Scenario** mean other things. In Tundra they are defined only as in this document (Role-or-System actor on a Process; business Contract text; end-to-end Scenario examples).

---

## The Six Core Concepts

### Roles

Named actors in the domain.  
A real person can hold several Roles at the same time (for example Account Holder and Beneficial Owner).  
Roles are declared explicitly so that rights and obligations attach clearly.

### Relationships

Named connections between Roles, or between a Role and a subject.  
They are written in plain English using the form “A is X of B”.

Examples:
- Seller is Owner of Listing
- Viewer is Follower of Author
- Editor is Assignee of Article

When the Role name and the relationship name are the same, the short form is allowed:

- Author of Post          (instead of “Author is Author of Post”)
- Owner of Listing        (instead of “Owner is Owner of Listing”)

Both forms are valid. Prefer the short form when the full form would repeat the same word.

Relationships are first-class so they can be referenced cleanly from Contracts and Processes instead of being buried in ad-hoc phrases.

### Contracts

The authoritative rules and obligations of the domain.  
They state who may do what, and under which conditions.  
Contracts are the single source of truth and must be written so a non-programmer can read them and an automated test can check them.

If a rule is inherently numerical or data-dependent, make the Contract as precise and measurable as you can (thresholds, roles, states). Do not embed executable code in the model.

### States

The meaningful situations that a **specific subject** can be in.

Every State must name its subject.  
Good: “Application is Automatically approved”, “Hours are in Draft”, “Invoice is Open”.  
Bad: “Automatically approved” (subject unclear).

States make progress visible and checkable.

### Processes

The named transformations that move a subject from one State to another.

Each Process must declare:

- **actor** — which Role performs it, or `System` for automatic steps  
  Do **not** list `System` under `roles:` — it is a reserved actor name, not a domain Role.  
- **requires** — one or more **declared States**, or a **genesis** condition before the subject exists:  
  `nothing`, `no <Subject> exists`, or `<Subject> does not exist`  
  **Every model needs at least one genesis Process** so a subject can come into existence.  
- **results** — resulting **declared State(s)** (string or list)

**List semantics**

| Field | List means | Example |
| --- | --- | --- |
| `requires` | **Any of** (OR) — Process may run if any listed State holds | Cancel when Order is Placed **or** Paid |
| `results` | **All of** (AND) — all listed outcomes apply | Create Invoice → Invoice is Open **and** Hours are Invoiced |

**Branch outcomes (XOR)** — when a Process has **mutually exclusive** endings for the same subject, do **not** list them under `results` (that would mean AND). Use `outcomes:` instead:

```yaml
- name: Make automatic credit decision
  actor: System
  requires: Application is Credit check completed
  outcomes:
    - when: debt-to-income is above 40% or the Applicant has betalningsanmärkningar
      results: Application is Automatically declined
    - when: debt-to-income is at or below 25% and no missed payments
      results: Application is Automatically approved
    - when: otherwise
      results: Application is Pending Loan Officer review
```

Rules: a Process has **`results` or `outcomes`, never both**; each branch needs `when` + `results`; at most one `otherwise`, and it must be last; `when` text follows the same testability discipline as Contracts.

**`requires` vs Contracts (`enforced_by`)**

| Concern | Prefer |
| --- | --- |
| Lifecycle / wrong state | `requires` (and `results` / `outcomes`) |
| Who may act, relationship, policy threshold | Contract text + optional `enforced_by` on the Process |

Do not restate the same state guard only as a Contract without a reason — use `requires` for state, Contracts for authority and policy.

### Scenarios

Concrete, end-to-end *examples* of walking through the process.

The process itself is defined by States + Processes + Contracts (and the Relationships they rely on).  
A Scenario is one specific path (happy path or important error path).

Scenarios are living documentation and the basis for generated tests.  
You can add many Scenarios without changing the underlying rules.

**Scenario vocabulary for contracts:**

| Situation | Phrase |
| --- | --- |
| An actor tries something forbidden | `And the contract "…" is broken` or `And the contract [id] is broken` |
| An automatic rule fires as designed | `And the contract "…" is applied` or `And the contract [id] is applied` |

Prefer colons in scenario names: `"Happy path: …"`, `"Error: …"`.  
Quoted text must match a declared Contract **exactly** (or use a stable `[id]`).

---

## Decorators

Optional fields on States or Processes when core concepts are not enough.

### Temporal and ordering

| Field | Where | Meaning | Example |
| --- | --- | --- | --- |
| `before` | process | Allowed only before a **time point** *or* before reaching a **named state fragment** (ordering gate) | `before: start time` · `before: Shipped` |
| `after` | process | Allowed only after a time point or named state fragment | `after: end time` |
| `expires_in` | state | State ends after a duration — pair with a **System** Process that requires this State | `expires_in: 15 minutes` |
| `within` | process | Relative time window | `within: 24 hours before start` |

Prefer clear time phrases (`start time`, `15 minutes`) for pure temporal rules.  
State-gate uses of `before` / `after` (e.g. `before: Shipped`) mean “while still before that lifecycle point.”

### Aggregational

| Field | Where | Meaning | Example |
| --- | --- | --- | --- |
| `capacity` | state | Maximum size | `capacity: 1` |
| `quantity` | state / process | Amount constraint | `quantity: at least 1` |
| `contains` | state | Collection held | `contains: LineItems` |

Decorators are optional and minimal. Prefer core concepts first.  
Do not invent decorator names outside this table.

---

## Exact output format (YAML)

Every model is a YAML document of this shape:

```yaml
tundra: <short name>

roles:
  - <Role name>

relationships:
  - <Role> is <Relationship> of <subject>

contracts:
  # thin form (still valid):
  - <testable plain-English rule>
  # or with stable id (preferred for implement / enforce links):
  - id: only-manager-creates-invoice
    text: Only the Manager may create an invoice
    source: stated          # or inferred (must confirm before export)
    rationale: optional why  # human context; not codegen

states:
  - <Subject is Some state>
  # or with decorators:
  - name: <Subject is Some state>
    expires_in: 15 minutes

processes:
  - name: <Process name>
    actor: <Role or System>
    requires: <State or genesis condition>   # or a list (OR)
    results: <State or short outcome>      # or a list (AND) — exclusive with outcomes
    # OR exclusive branches:
    # outcomes:
    #   - when: <condition>
    #     results: <State>
    #   - when: otherwise
    #     results: <State>
    enforced_by:                          # optional; Contract ids that govern this Process
      - only-manager-creates-invoice
    # optional: before, after, within, quantity, …

scenarios:
  - name: "Happy path: …"
    steps:
      - Given …
      - When the <Role> …
      - Then …
  - name: "Error: …"
    steps:
      - Given …
      - When the <Role> tries to …
      - Then …
      - And the contract "…" is broken

```

Structural rules are enforced by [`schema/tundra.schema.json`](schema/tundra.schema.json).

---

## Good example

```yaml
tundra: Consultant hours to client invoice

roles:
  - Consultant
  - Manager
  - Client

relationships:
  - Consultant is Owner of Hours
  - Manager is Creator of Invoice
  - Client is Recipient of Invoice

contracts:
  - Hours may be edited by the Consultant only while they are in Draft
  - Once hours are Submitted they become immutable for the Consultant
  - An invoice may be created only from Submitted hours that have not already been invoiced
  - Only the Client may Approve or Dispute an open invoice
  - Only the Manager may create an invoice

states:
  - Hours are in Draft
  - Hours are Submitted
  - Hours are Invoiced
  - Invoice is Open
  - Invoice is Approved
  - Invoice is Disputed

processes:
  - name: Register Hours
    actor: Consultant
    requires: no hours exist
    results: Hours are in Draft
  - name: Edit Hours
    actor: Consultant
    requires: Hours are in Draft
    results: Hours are in Draft
  - name: Submit Hours
    actor: Consultant
    requires: Hours are in Draft
    results: Hours are Submitted
  - name: Create Invoice
    actor: Manager
    requires: Hours are Submitted
    results:
      - Invoice is Open
      - Hours are Invoiced
  - name: Approve Invoice
    actor: Client
    requires: Invoice is Open
    results: Invoice is Approved
  - name: Dispute Invoice
    actor: Client
    requires: Invoice is Open
    results: Invoice is Disputed

scenarios:
  - name: "Happy path: hours submitted and invoice approved"
    steps:
      - Given no hours exist
      - When the Consultant registers hours
      - Then the Hours are in Draft
      - When the Consultant submits the hours
      - Then the Hours are Submitted
      - And the hours can no longer be edited by the Consultant
      - When the Manager creates an invoice from the submitted hours
      - Then the Invoice is Open
      - And the Hours are Invoiced
      - When the Client approves the invoice
      - Then the Invoice is Approved

  - name: "Error: Consultant tries to edit hours after submission"
    steps:
      - Given the Hours are Submitted
      - When the Consultant tries to edit the hours
      - Then the edit is rejected
      - And the Hours remain Submitted
      - And the contract "Hours may be edited by the Consultant only while they are in Draft" is broken

  - name: "Error: Consultant tries to create an invoice"
    steps:
      - Given the Hours are Submitted
      - When the Consultant tries to create an invoice
      - Then invoice creation is rejected
      - And the Hours remain Submitted
      - And the contract "Only the Manager may create an invoice" is broken

```

Full file: [`examples/consultant-hours/consultant-hours-invoice.tundra`](examples/consultant-hours/consultant-hours-invoice.tundra).

---

## Counter-examples (what to avoid)

**Bad: Vague Contracts**

```yaml
contracts:
  - The system should be secure
  - The loan is too high relative to income

```
→ Every Contract must be precise enough to test (thresholds, named conditions, explicit roles).

**Bad: Roles only buried in Contracts**  
→ Declare the Role under `roles:`.

**Bad: Inventing knowledge**  
→ Ask clarifying questions instead.

**Bad: Fat models**  
→ Prefer many small, focused models.

**Bad: Processes without actor / requires / results**  

```yaml
processes:
  - Submit Hours   # invalid

```
→ Use a map with `name`, `actor`, `requires`, `results`.

**Bad: Embedding executable code in the model**

```yaml
contracts:
  - Only a platform admin may suspend a Listing
    # Do not attach SQL, Python, or other implementations here

```
→ Keep Contracts plain English; encode checks in generated code.

**Bad: Invalid or non-YAML structure**  
→ Models must be valid YAML matching the format above (and `schema/tundra.schema.json`).

---

## Key rules

1. **Never invent important knowledge.** Ask when unclear.  
2. **Prefer thin models.**  
3. **Contracts are plain language and testable.** No embedded code.  
4. **Roles are first-class.**  
5. **Relationships are first-class.**  
6. **Every State names its subject.**  
7. **Processes declare actor, requires, and results.** Actor is a Role or `System` (not listed under `roles:`).  
8. **Prefer Contract ids + `enforced_by`** on Processes so implementers do not re-infer which rule guards which step. Bare string Contracts remain valid for thin models.  
9. **Consistency across models.** No silent near-synonyms.  
10. **Scenarios demonstrate Contracts.** Use `is broken` / `is applied` with exact quotes or `[id]`.  
11. **Decorators are optional and minimal** — only the fields listed above.  
12. **Models are valid YAML** and should pass `tools/check_tundra.py`.

---

## How Tundra maps to code

| Tundra | In code |
| --- | --- |
| Role | Actor type / enum passed into process functions |
| Relationship | Ownership / association checks |
| Contract | Fail-fast check; error message quotes the Contract text |
| State | Enum (or equivalent) **per subject** |
| Process | One function/method; guard with actor + requires; return results |
| Decorator | Time / capacity / quantity fields |
| Scenario | Executable test or demo script |

---

## Why these six concepts?

They give the properties that matter most for durable **domain obligations**:

- Explicit knowledge (no coincidence)
- Single source of truth (DRY)
- Clear actors and connections (Roles + Relationships)
- Clear obligations (Design by Contract)
- Visible progress (States + Processes)
- Living examples that become tests (Scenarios)
- Easy to change, even by non-programmers (ETC)

They do **not** cover every property of good long-running software. See [Scope and blindspots](docs/scope-and-blindspots.md).

---

## Scope and blindspots

Tundra is intentionally narrow. It is not a complete methodology for building software.

**What it is for:** business process knowledge — who may do what, under which conditions, how a subject moves through meaningful States, and how you demonstrate that with Scenarios.

**What it is not:** a data model, architecture diagram, NFR catalog, threat model, UX spec, ops runbook, or full test strategy.

Fuller map: [`docs/scope-and-blindspots.md`](docs/scope-and-blindspots.md).

---

## Background and principles

Tundra is heavily inspired by the ideas in *The Pragmatic Programmer* by Dave Thomas and Andy Hunt.

Key principles: Easy to Change (ETC), DRY, Design by Contract, No Coincidence, Tracer Bullets / Feedback, Orthogonality.

> Dave Thomas & Andy Hunt  
> *The Pragmatic Programmer: Your Journey to Mastery*  
> (20th Anniversary Edition recommended)
