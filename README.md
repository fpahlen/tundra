# Tundra

A plain-English language for specifying business processes with explicit roles, testable contracts, and executable scenarios.

**Tundra captures who may do what, under which conditions, and how you prove it** — so humans and AIs can share one model of the business without treating source code as the only source of truth.

As AI writes more of the code, durable knowledge must live *above* the code. Tundra is that layer: thin models, explicit obligations, and living examples that become tests.

Files use the suffix `.tundra`.

---

## Why Tundra?

Most teams either bury rules in code (invisible to non-programmers) or scatter them across tickets and wikis (invisible to machines). Tundra sits in between:

| Audience | What they get |
|----------|----------------|
| Humans | Plain language they can read, challenge, and change |
| AIs | Structure disciplined enough to extract, validate, and implement without inventing rules |
| Both | A common language for *good* software: explicit knowledge, single source of truth, design by contract |

A whole system is normally many **small** models, not one giant file.

---

## The Five Core Concepts

### Roles

Named actors in the domain.  
A real person can hold several Roles at the same time (for example Account Holder and Beneficial Owner).  
Roles are declared explicitly so that rights and obligations attach clearly.

### Contracts

The authoritative rules and obligations of the domain.  
They state who may do what, and under which conditions.  
Contracts are the single source of truth and must be written so a non-programmer can read them and an automated test can check them.

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

The process itself is defined by States + Processes + Contracts.  
A Scenario is one specific path (happy path or important error path).

Scenarios are living documentation and the basis for generated tests.  
You can add many Scenarios without changing the underlying rules.

**Scenario vocabulary for contracts:**

| Situation | Phrase |
|-----------|--------|
| An actor tries something forbidden | `And the contract "…" is broken` |
| An automatic rule fires as designed | `And the contract "…" is applied` |

---

## Exact Output Format

Every model must use this structure:

```text
Tundra: <short name>

  Roles:
    - <Role name>
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

---

## Key Rules

1. **Never invent important knowledge.**  
   If something is unclear, ask a clarifying question.

2. **Prefer thin models.**  
   Only include what is needed for the described behaviour.

3. **Contracts are plain language and testable.**  
   A non-programmer must be able to challenge them; a test must be able to check them.

4. **Roles are first-class.**  
   Declare them explicitly. A person can hold multiple Roles.

5. **Every State must name its subject.**  
   Write “Application is Automatically approved”, not just “Automatically approved”.

6. **Processes declare Actor, Requires, and Results.**  
   Use a declared Role or `System` as Actor.

7. **Consistency across models.**  
   When existing models are provided, treat their Roles and Contracts as authoritative.  
   Do not silently create near-synonyms.

8. **Scenarios demonstrate the Contracts.**  
   At least one happy-path Scenario and the most important error Scenarios should be present.  
   Use `is broken` for forbidden actions and `is applied` for automatic rules that fire correctly.

---

## How Tundra maps to code

| Tundra | In code |
|--------|---------|
| Role | Actor type / enum passed into process functions |
| Contract | Fail-fast check; error message quotes the Contract text |
| State | Enum (or equivalent) **per subject** — do not collapse unrelated subjects into one enum |
| Process | One function/method; guard with Actor + Requires; return Results |
| Scenario | Executable test or demo script |

Roles are not decoration: if a Contract says “Only the Manager may…”, the implementation must take an actor and reject the wrong Role.

---

## Using the prompt pack

This repository includes three prompts under `prompts/`. They form a loop:

```text
Human intent  →  extract-tundra  →  .tundra model(s)
                      ↓
                validate-tundra  →  quality report
                      ↓
                implement-tundra →  code + scenario tests
```

| Prompt | Job |
|--------|-----|
| [`prompts/extract-tundra.md`](prompts/extract-tundra.md) | Turn messy human description into a thin `.tundra` model (or ask clarifying questions) |
| [`prompts/validate-tundra.md`](prompts/validate-tundra.md) | Check testability, structure, coverage, and cross-model consistency |
| [`prompts/implement-tundra.md`](prompts/implement-tundra.md) | Generate faithful code and tests from a model |

Always treat this README as the definition of Tundra when using the prompts.

### House models

| Model | Purpose |
|-------|---------|
| [`models/consultant-hours-invoice.tundra`](models/consultant-hours-invoice.tundra) | Clean reference model (also implemented under `examples/`) |
| [`models/loan-application-entry.tundra`](models/loan-application-entry.tundra) | Domain-rich example; **intentionally includes vague Contracts** so `validate-tundra` has known findings to report |

### Runnable example

See [`examples/consultant-hours/`](examples/consultant-hours/) for Python and C implementations that enforce Roles and Contracts (happy path + error paths).

---

## Why these five concepts?

They give the properties that matter most for durable **domain obligations**:

- Explicit knowledge (no coincidence)
- Single source of truth (DRY)
- Clear obligations (Design by Contract)
- Visible progress (States + Processes)
- Living examples that become tests (Scenarios)
- Easy to change, even by non-programmers (ETC)

They do **not** cover every property of good long-running software. See [Scope and blindspots](#scope-and-blindspots).

---

## Scope and blindspots

Tundra is intentionally narrow. It is not a complete methodology for building software.

### What it is for

**Business process knowledge:** who may do what, under which conditions, how a subject moves through meaningful States, and how you demonstrate that with Scenarios.

That is where long-lived business systems often lose knowledge — buried in code, tickets, or one expert’s head.

### What it is not

Tundra is not a data model, architecture diagram, NFR catalog, threat model, UX spec, ops runbook, or full test strategy.  
If your main risk is throughput, cryptography, pure analytics, or pixel-level UX, start with other tools and use Tundra only where **obligations and lifecycles** matter.

### Known blindspots

These are real gaps. Name them so teams pair Tundra with the right companions instead of forcing everything into Contracts.

| Blindspot | What Tundra under-specifies | Pair with |
|-----------|----------------------------|-----------|
| **Data shape & invariants** | Cardinality, sums, uniqueness, “what identifies this subject” | Schema, constraints, domain types, property tests |
| **Time, history & audit** | States are *current*; who changed what when; as-of / effective dating | Event log, audit tables, temporal models |
| **Concurrency** | Models read as one case (“the invoice”); races, retries, multi-instance | Explicit contention Scenarios, locking/idempotency design |
| **Failure beyond “contract broken”** | Downstream timeouts, partial failure, compensation, degraded mode | Retries, sagas, supervision, circuit breakers |
| **Money & calculations** | Discrete state hops dominate; rounding, interest, premiums | Formulas + golden tests |
| **Reads, reporting & reconciliation** | Write/process oriented; weak on extracts and “does A match B?” | Query contracts, reconciliations, report specs |
| **Rule evolution** | Timeless snapshot; grandfathering, dual-running policy, in-flight migration | Versioned rules / effective dates outside or beside the model |
| **Model composition** | Many thin models encouraged; binding between them (IDs, events) is light | Explicit cross-model links and shared Role/Contract names |
| **Long human waits** | Processes look like immediate steps; timers, reminders, escalations | Operational SLAs, workflow timers elsewhere |
| **Scenarios ≠ full verification** | Tracer-bullet examples, not exhaustive coverage | Property, load, migration, and chaos tests as needed |

Also easy to miss: side obligations on a transition (letters, GDPR erasure, “document the decision”), fairness of automated decisions, and production observability (did this Process run?).

### Biases we admit

Tundra leans toward **case workflow**, **stakeholder-readable rules**, and **plain language** — shaped by enterprise process domains and a preference for Eloquent, changeable knowledge over ceremony.

It under-exports concerns that also keep systems alive for decades: **structural data correctness**, **runtime resilience**, and **set-based / batch** work.  
“Actor” means a **Role** (who is allowed to act), not an OTP process or concurrent runtime actor.

For a longer discussion, see [`docs/scope-and-blindspots.md`](docs/scope-and-blindspots.md).

### Bad: stuffing unrelated quality into Contracts

```text
Contracts:
  - The API p99 latency must be under 200ms
  - The system must be secure
  - The UI should feel snappy
```

→ Wrong tool. Keep Contracts for domain obligations you can demonstrate in Scenarios; put SLOs, threat models, and UX criteria in their own artifacts.

---

## Background and principles

Tundra is heavily inspired by *The Pragmatic Programmer* by Dave Thomas and Andy Hunt.

| Principle | How Tundra uses it |
|-----------|-------------------|
| **Easy to Change (ETC)** | Thin, localized models; minimal ripple when a rule changes |
| **DRY** | Contracts are the single authoritative statement of a rule |
| **Design by Contract** | Obligations are explicit; violations fail early and clearly |
| **No Coincidence** | Behaviour comes from declared rules, not accidental conditions |
| **Tracer Bullets** | Scenarios are thin end-to-end paths that give real feedback |
| **Orthogonality** | Unrelated concerns live in separate models |

The language turns those ideas into a form both humans and AIs can use between intent and code.

For deeper reading:

> Dave Thomas & Andy Hunt  
> *The Pragmatic Programmer: Your Journey to Mastery*  
> (20th Anniversary Edition recommended)

---

## Roadmap

The near-term product direction is a small site that **interviews** a human and produces a set of `.tundra` files, using the same extract/validate discipline as this pack. Later: point at a GitHub repo or codebase and **extract** the Tundras implied by existing behaviour. This repository remains the methodology source of truth those tools should consume.

---

## License

MIT — see [LICENSE](LICENSE).
