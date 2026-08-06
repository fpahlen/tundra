# Tundra

A plain-English language for specifying business processes with explicit roles, testable contracts, and executable scenarios.

Tundra is a simple, language-agnostic way to capture business knowledge so that both humans and AIs can read, challenge, and evolve it.

It sits between human intent and generated code.  
The goal is to keep knowledge explicit, localized, and easy to change.

Models are deliberately thin.  
A whole system is normally made of many small models rather than one large model.

Files use the suffix `.tundra`.

---

## The Five Core Concepts

### Roles
Named actors in the domain.  
A real person can hold several Roles at the same time (for example Account Holder and Beneficial Owner).  
Roles are declared explicitly so that rights and obligations can be attached clearly and consistently.

### Contracts
The authoritative rules and obligations of the domain.  
They state who may do what, and under which conditions.  
Contracts are the single source of truth and must be written in plain language that a non-programmer can read and challenge.

### States
The meaningful situations that a specific subject can be in.  

Every State must name its subject explicitly so there is no ambiguity about what is in that state.  
Good examples: “Application is Automatically approved”, “Hours are in Draft”, “Invoice is Open”.  

States make the progress of the process visible and checkable.

### Processes
The named transformations that move the subject from one State to another.  
Each Process should have clear preconditions and results expressed through the Contracts and States.

### Scenarios
Concrete, end-to-end *examples* of walking through the business process.  

The actual business process is defined by States + Processes + Contracts.  
A Scenario is one specific path through that process (usually a happy path or an important error path).  

Scenarios show the Roles, Contracts, States and Processes in action, serve as living documentation, and become the basis for generated tests.  
You can have many Scenarios for the same process without changing the underlying rules.

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
    - <state 1>
    - <state 2>
    ...

  Processes:
    - <process 1>
    - <process 2>
    ...

  Scenario: <name of happy path>
    Given ...
    When ...
    Then ...
    ...

  Scenario: <name of important error path>
    Given ...
    When ...
    Then ...
    And the contract "..." is broken
```

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
    - Invoice is Open
    - Invoice is Approved
    - Invoice is Disputed

  Processes:
    - Register Hours
    - Edit Hours
    - Submit Hours
    - Create Invoice
    - Approve Invoice
    - Dispute Invoice

  Scenario: Happy path – hours submitted and invoice approved
    Given no hours exist
    When the Consultant registers hours
    Then the Hours are in Draft

    When the Consultant submits the hours
    Then the Hours are Submitted
    And the hours can no longer be edited by the Consultant

    When the Manager creates an invoice from the submitted hours
    Then the Invoice is Open

    When the Client approves the invoice
    Then the Invoice is Approved

  Scenario: Error – Consultant tries to edit hours after submission
    Given the Hours are Submitted
    When the Consultant tries to edit the hours
    Then the edit is rejected
    And the Hours remain Submitted
    And the contract "Hours may be edited by the Consultant only while they are in Draft" is broken
```

---

## Counter-Examples (what to avoid)

**Bad: Vague or missing Contracts**
```text
Contracts:
  - The system should be secure
  - Users can do things
```
→ Too vague. A Contract must be specific enough that it can be checked.

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

**Bad: Inconsistent naming across models**
Calling the same actor “User” in one model and “Customer” in another without reason.  
→ Reuse existing Role names whenever possible.

---

## Key Rules

1. **Never invent important knowledge.**  
   If something is unclear, ask a clarifying question.

2. **Prefer thin models.**  
   Only include what is actually needed for the described behaviour.

3. **Contracts are written in plain language.**  
   A non-programmer must be able to read and challenge them.

4. **Roles are first-class.**  
   Declare them explicitly. A person can hold multiple Roles.

5. **Every State must name its subject.**  
   Write “Application is Automatically approved”, not just “Automatically approved”.

6. **Consistency across models.**  
   When existing models are provided, treat their Roles and Contracts as authoritative.  
   Do not silently create near-synonyms.

7. **Scenarios demonstrate the Contracts.**  
   At least one happy-path Scenario and the most important error Scenarios should be present.

---

## Why these five concepts?

They give us the properties that matter most for long-lived systems:

- Explicit knowledge (no coincidence)
- Single source of truth (DRY)
- Clear obligations (Design by Contract)
- Visible progress (States + Processes)
- Living examples that can become tests (Scenarios)
- Easy to change, even by non-programmers

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

The language tries to make these principles concrete and usable by both humans and AIs.  
It turns the pragmatic ideas into a simple, structured form that sits between human intent and generated code.

For deeper reading, see:

> Dave Thomas & Andy Hunt  
> *The Pragmatic Programmer: Your Journey to Mastery*  
> (20th Anniversary Edition recommended)
