# Tundra

A plain-English language for specifying business processes with explicit roles, relationships, testable contracts, and executable scenarios.

**Tundra captures who may do what, under which conditions, and how you prove it** — so humans and AIs can share one model of the business without treating source code as the only source of truth.

As AI writes more of the code, durable knowledge must live *above* the code. Tundra is that layer: thin models, explicit obligations, and living examples that become tests.

Models are deliberately thin.  
A whole system is normally made of many small models rather than one large model.

Files use the suffix `.tundra`.

## Examples

Worked models live under [`examples/`](examples/).  
See [`examples/README.md`](examples/README.md) for the full catalog.

---

## Why Tundra?

Most teams either bury rules in code (invisible to non-programmers) or scatter them across tickets and wikis (invisible to machines). Tundra sits in between:

| Audience | What they get |
|----------|----------------|
| Humans | Plain language they can read, challenge, and change |
| AIs | Structure disciplined enough to extract, validate, and implement without inventing rules |
| Both | A common language for *good* software: explicit knowledge, single source of truth, design by contract |

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

Each Process should declare:

- **Actor** — which Role (or `System` for automatic steps) performs it  
- **Requires** — precondition State(s) or a short condition tied to a Contract  
- **Results** — resulting State(s)

### Scenarios

Concrete, end-to-end *examples* of walking through the process.

The process itself is defined by States + Processes + Contracts (and the Relationships they rely on).  
A Scenario is one specific path (happy path or important error path).

Scenarios are living documentation and the basis for generated tests.  
You can add many Scenarios without changing the underlying rules.

**Scenario vocabulary for contracts:**

| Situation | Phrase |
|-----------|--------|
| An actor tries something forbidden | `And the contract "…" is broken` |
| An automatic rule fires as designed | `And the contract "…" is applied` |

---

## Decorators

The six core concepts cover most business knowledge.  
When they are not enough, Tundra provides temporal and aggregational decorators.

### Temporal decorators

| Decorator | Where | Meaning | Example |
|-----------|-------|---------|---------|
| `@before` | Process | Allowed only before a point in time | `@before start time` |
| `@after` | Process | Allowed only after a point in time | `@after end time` |
| `@expires-in` | State | State ends automatically after a duration | `@expires-in 15 minutes` |
| `@within` | Process | Allowed only inside a relative window | `@within 24 hours before start` |

### Aggregational decorators

| Decorator | Where | Meaning | Example |
|-----------|-------|---------|---------|
| `@capacity` | State | Maximum size | `@capacity 12` |
| `@quantity` | State / Process | Current or required quantity | `@quantity at least 1` |
| `@contains` | State | Holds a collection | `@contains LineItems` |

Decorators are optional and minimal. Prefer core concepts first.

---

## Exact Output Format

Every model must use this structure:

```text
Tundra: <short name>

  Roles:
    - <Role name>
    - ...

  Relationships:
    - <Role> is <Relationship> of <subject>
    - ...

  Contracts:
    - <contract 1>
    - <contract 2>
    ...

  States:
    - <State that names its subject>
    - ...

  Processes:
    - <Process name>
        Actor: <Role or System>
        Requires: <State or short condition>
        Results: <State or short outcome>
    - ...

  Scenario: <name of happy path>
    Given ...
    When the <Role> ...
    Then ...
    ...

  Scenario: <name of important error path>
    Given ...
    When the <Role> tries to ...
    Then ...
    And the contract "..." is broken
```

`Actor`, `Requires`, and `Results` are plain English under each Process.  
They are required for quality house models and for extract/implement prompts; they keep transitions explicit without turning Tundra into a programming language.

---

## Good Example

```text
Tundra: Consultant hours to client invoice

  Roles:
    - Consultant
    - Manager
    - Client

  Relationships:
    - Consultant is Owner of Hours
    - Manager is Creator of Invoice
    - Client is Recipient of Invoice

  Contracts:
    - Hours may be edited by the Consultant only while they are in Draft
    - Once hours are Submitted they become immutable for the Consultant
    - An invoice may be created only from Submitted hours that have not already been invoiced
    - Only the Client may Approve or Dispute an open invoice
    - Only the Manager may create an invoice

  States:
    - Hours are in Draft
    - Hours are Submitted
    - Hours are Invoiced
    - Invoice is Open
    - Invoice is Approved
    - Invoice is Disputed

  Processes:
    - Register Hours
        Actor: Consultant
        Requires: no hours exist
        Results: Hours are in Draft
    - Edit Hours
        Actor: Consultant
        Requires: Hours are in Draft
        Results: Hours are in Draft
    - Submit Hours
        Actor: Consultant
        Requires: Hours are in Draft
        Results: Hours are Submitted
    - Create Invoice
        Actor: Manager
        Requires: Hours are Submitted
        Results: Invoice is Open; Hours are Invoiced
    - Approve Invoice
        Actor: Client
        Requires: Invoice is Open
        Results: Invoice is Approved
    - Dispute Invoice
        Actor: Client
        Requires: Invoice is Open
        Results: Invoice is Disputed

  Scenario: Happy path – hours submitted and invoice approved
    Given no hours exist
    When the Consultant registers hours
    Then the Hours are in Draft

    When the Consultant submits the hours
    Then the Hours are Submitted
    And the hours can no longer be edited by the Consultant

    When the Manager creates an invoice from the submitted hours
    Then the Invoice is Open
    And the Hours are Invoiced

    When the Client approves the invoice
    Then the Invoice is Approved

  Scenario: Error – Consultant tries to edit hours after submission
    Given the Hours are Submitted
    When the Consultant tries to edit the hours
    Then the edit is rejected
    And the Hours remain Submitted
    And the contract "Hours may be edited by the Consultant only while they are in Draft" is broken

  Scenario: Error – Consultant tries to create an invoice
    Given the Hours are Submitted
    When the Consultant tries to create an invoice
    Then invoice creation is rejected
    And the Hours remain Submitted
    And the contract "Only the Manager may create an invoice" is broken
```

---

## Counter-Examples (what to avoid)

**Bad: Vague or missing Contracts**
```text
Contracts:
  - The system should be secure
  - Users can do things
  - The loan is too high relative to income
```
→ Too vague. A Contract must be specific enough that a clear automated test can be written (thresholds, named conditions, explicit roles).

**Bad: Roles hidden only inside Contracts**
```text
Contracts:
  - The person who registered the hours can edit them until submission
```
→ Declare the Role (“Consultant”) explicitly in the Roles section.

**Bad: Inventing knowledge**
Creating States or Contracts that were never mentioned by the human.  
→ Always ask a clarifying question instead.

**Bad: Fat models**
Putting authentication, invoicing, reporting and user management into one giant file.  
→ Prefer many small, focused models.

**Bad: Processes without Actor / Requires / Results**
A bare list of process names forces implementers to guess transitions.  
→ State who acts, what must already be true, and what changes.

**Bad: Inconsistent naming across models**
Calling the same actor “User” in one model and “Customer” in another without reason.  
→ Reuse existing Role names whenever possible.

**Bad: Embedding code in the model**
```text
Contracts:
  - Only a platform admin may suspend a Listing
      guard:
        sql: exists (select 1 from users ...)
```
→ Keep the model plain English. Express the rule as a precise Contract; let implementations encode the check.

---

## Key Rules

1. **Never invent important knowledge.**  
   If something is unclear, ask a clarifying question.

2. **Prefer thin models.**  
   Only include what is needed for the described behaviour.

3. **Contracts are plain language and testable.**  
   A non-programmer must be able to challenge them; a test must be able to check them.  
   Do not embed SQL, Python, or other executable code in the model.

4. **Roles are first-class.**  
   Declare them explicitly. A person can hold multiple Roles.

5. **Relationships are first-class.**  
   Declare named connections between Roles or between a Role and a subject.  
   Reference them from Contracts and Processes instead of using ad-hoc phrases.

6. **Every State must name its subject.**  
   Write “Application is Automatically approved”, not just “Automatically approved”.

7. **Processes declare Actor, Requires, and Results.**  
   Use a declared Role or `System` as Actor.

8. **Consistency across models.**  
   When existing models are provided, treat their Roles, Relationships and Contracts as authoritative.  
   Do not silently create near-synonyms.

9. **Scenarios demonstrate the Contracts.**  
   At least one happy-path Scenario and the most important error Scenarios should be present.  
   Use `is broken` for forbidden actions and `is applied` for automatic rules that fire correctly.

10. **Decorators are optional and minimal.**  
    Use temporal and aggregational decorators only when the core concepts are not enough.

---

## How Tundra maps to code

| Tundra | In code |
|--------|---------|
| Role | Actor type / enum passed into process functions |
| Relationship | Ownership / association checks before a Process is allowed |
| Contract | Fail-fast check; error message quotes the Contract text |
| State | Enum (or equivalent) **per subject** — do not collapse unrelated subjects into one enum |
| Process | One function/method; guard with Actor + Requires; return Results |
| Decorator | Time windows, capacity, quantity, or collection fields |
| Scenario | Executable test or demo script |

Roles are not decoration: if a Contract says “Only the Manager may…”, the implementation must take an actor and reject the wrong Role.

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

## Background and Principles

Tundra is heavily inspired by the ideas in *The Pragmatic Programmer* by Dave Thomas and Andy Hunt.

Key principles from the book that shaped it:

- **Easy to Change (ETC)** – The primary measure of design quality. Knowledge must be localized so that a change has minimal ripple effects.
- **DRY (Don’t Repeat Yourself)** – Every piece of knowledge must have a single, authoritative representation.
- **Design by Contract** – Obligations between parties should be explicit. Violations should be detected early and clearly.
- **No Coincidence** – Code (and models) should work because of deliberate design, not because of accidental conditions.
- **Tracer Bullets / Feedback** – Prefer thin, end-to-end paths that give real feedback early (this is why Scenarios exist).
- **Orthogonality** – Keep unrelated things independent so they can change independently.

For deeper reading, see:

> Dave Thomas & Andy Hunt  
> *The Pragmatic Programmer: Your Journey to Mastery*  
> (20th Anniversary Edition recommended)
