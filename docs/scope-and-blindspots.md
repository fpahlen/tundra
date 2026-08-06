# Scope and blindspots

Tundra does not try to be a perfect methodology for every software project.  
This note is for humans (and AIs) who want to know **what it optimizes for**, **what it leaves out**, and **what to use alongside it**.

The short version lives in the [README](../README.md#scope-and-blindspots). This page is the fuller map.

---

## Center of gravity

Tundra is excellent at one slice of good long-running software:

> **Business obligations around who may change what, under which conditions, with visible progress and living examples.**

| Strength | Mechanism |
|----------|-----------|
| Explicit business rules | Contracts |
| Authorization as domain knowledge | Roles + Process Actor |
| Lifecycle clarity | States (subject named) + Processes |
| Proof and feedback | Scenarios |
| Change locality | Thin models, DRY Contracts |
| Shared human + AI surface | Plain English + fixed structure |

That is a **workflow / case-management / design-by-contract** lens. It matches much of banking and insurance *case* work (applications, approvals, four-eyes) and the Pragmatic Programmer idea that knowledge should live in one authoritative place.

It is **not** a complete theory of good software.

---

## Where the shape of Tundra comes from

Methodologies carry the biases of their authors. Naming them is better than pretending neutrality.

### Readable languages and clear domain models

Values that show up strongly:

- Eloquence over ceremony → plain-English Contracts  
- Immutability as a *business* virtue → e.g. “Submitted hours are immutable”  
- Thin, orthogonal pieces → many small models  
- Happiness and clarity → hostility to vague corporate-speak  

Shadow sides:

- Weaker push toward machine-checkable structure (types, units, schemas)  
- Easy to stay narrative and miss quantitative invariants  
- Runtime resilience (supervision, isolation, restarts) is not a first-class concept  
- **Actor** means Role, not an OTP / actor-model concurrent process — easy vocabulary collision  

### Case-heavy enterprise work (banking, insurance, SQL consulting)

Values that show up strongly:

- Who may do what; approval chains; compliance-flavored steps  
- Linear stakeholder Scenarios (“happy path”, important error path)  
- Single-case language (“the Application”, “the Invoice”)  

Shadow sides (often ironic for people who live in SQL):

- **Data shape and set correctness** underplayed relative to process  
- Batch / overnight / portfolio operations underplayed  
- Audit *history* and temporal reporting underplayed  
- Reconciliation and regulatory extracts underplayed  

A long-lived bank or insurer dies from wrong *data and money* as often as from wrong *workflow*. Tundra currently speaks more to the second.

---

## Blindspots in detail

### 1. Data shape and structural invariants

Tundra answers “what state is this case in?” better than “what must always be true about the data?”

Under-specified:

- Cardinality (“exactly one primary insured”)  
- Aggregations (“sum of lines equals header”)  
- Uniqueness, referential integrity, orphan rules  
- Identity: what *is* a batch of hours? What identifies an invoice?  

**Pair with:** relational schema, CHECK constraints, domain types, property-based tests.

### 2. Time, history, and audit

States describe the **current** situation. Many regulated systems are **temporal**:

- Who changed what, when  
- As-of reporting, effective dating, retroactive correction  
- Retention and “right to be forgotten” vs audit keep  

A Contract like “UC check may be reused only if less than 6 months old” is time-aware, but Tundra has no general pattern for history.

**Pair with:** event logs, audit tables, temporal or bitemporal models.

### 3. Concurrency and multi-instance reality

House examples read as one subject at a time. Production has:

- Many concurrent cases  
- Two actors on the same subject  
- Retries and “already invoiced” races  

You *can* write a Scenario for a race; the methodology does not force the question.

**Pair with:** explicit contention Scenarios, idempotency keys, locking or version checks.

### 4. Failure outside “contract broken”

Tundra failures are **domain rule violations**. Systems also fail when:

- BankID or UC times out  
- A message is delivered twice  
- A step succeeds locally and fails downstream  
- You must run degraded (“accept now, credit-check later”)  

**Pair with:** timeouts, retries, sagas/compensation, supervision trees, circuit breakers.

### 5. Money, quantities, and calculations

Discrete state hops dominate. Weak on:

- Rounding modes, currency, interest, fees  
- Premium or settlement formulas  
- Golden-file expected amounts  

**Pair with:** explicit formulas, fixed test vectors, decimal discipline in code.

### 6. Reads, reporting, and reconciliation

Tundra is **write / process** oriented. Long-running enterprises also need:

- “All open invoices older than 30 days”  
- Ledger A must match system B  
- Regulatory extracts  

**Pair with:** query specs, reconciliation jobs, report contracts (their own artifacts).

### 7. Evolution of rules over time

A `.tundra` file is a **timeless snapshot**. Real calendars bring:

- Grandfathering existing contracts under old rules  
- Dual-running policy versions  
- Migrating in-flight States when a Process disappears  

**Pair with:** versioned policy, effective dates, migration playbooks.

### 8. Composition between models

“Prefer many thin models” is right for ETC. Underspecified:

- How Hours binds to Invoice (identifiers, events)  
- Shared Roles and Contracts across files  
- Order of implementation when models depend on each other  

**Pair with:** explicit cross-links in prose, stable IDs, a small index of models in the system.

### 9. Long human waits and escalations

Processes look like steps in a script. Real cases wait days:

- Reminders, SLAs, escalation to another Role  
- Calendar time vs processing time  

**Pair with:** operational workflow tools, timers, SLA monitors — optionally Scenarios that name elapsed time.

### 10. Scenarios are examples, not a full test strategy

Scenarios are **tracer bullets** (deliberate). They are not:

- Property-based coverage  
- Load or chaos tests  
- Migration or backup restore tests  

**Pair with:** the rest of a serious test strategy.

### Other easy misses

- **Side obligations** on a transition (customer letter, adverse-action notice, “decision must be documented”)  
- **Fairness / appeal** of automated decisions  
- **Observability** (business metrics, traces: did this Process run in prod?)  
- **“System” as Actor** can hide batch job vs callback vs message handler failure modes  
- **Vocabulary collision:** Actor, Process, Contract, Scenario mean other things in UML, BPMN, classical DbC, and OTP  

---

## Deliberately out of scope

Do not expect Tundra to replace:

| Concern | Better home |
|---------|-------------|
| Latency, capacity, cost SLOs | SLOs, load tests, capacity plans |
| Deep security (beyond who may act) | Threat models, controls, review |
| UX, accessibility, visual design | Design systems, UX research |
| CI/CD, feature flags, deploy | Platform / delivery docs |
| Team ownership (Conway) | Org design, team APIs |
| Full formal verification | Proof tools, not plain English |

Rejecting “the system should be secure” as a Contract is correct. That does not mean security is unimportant — it means it is **not this format**.

---

## Pragmatic Programmer principles vs this lens

Tundra operationalizes well for **domain rules**:

- Easy to Change (thin models)  
- DRY (Contracts as authority)  
- Design by Contract (obligations)  
- No Coincidence (declared rules)  
- Tracer Bullets (Scenarios)  
- Orthogonality (separate models)  

Less served by the five concepts alone:

- Reversibility of *rule and data* evolution  
- Runtime orthogonality (independent failure)  
- Security as a layered concern  
- Concurrency  
- Data as a long-lived asset (schema ≠ States)  

Tundra is a **focused operationalization** of a subset of good practice, not a re-encode of the whole book.

---

## Practical guidance

1. Use Tundra where **obligations and lifecycles** are the knowledge you keep losing.  
2. Keep Contracts testable and process-shaped; do not smuggle SLOs or vibes into them.  
3. When a blindspot is material to *your* system, create a **companion artifact** — do not grow the five concepts into twelve.  
4. In interviews or workshops, after the Tundra model is solid, ask:  
   - What must always be true about the **data**?  
   - What do we **log** for audit?  
   - What if **two people** act at once?  
   - What if a **dependency is down**?  
   - What **calculations** must be golden-tested?  
   - What **reports** must reconcile?  
   - What happens to **in-flight cases** when a rule changes?  

Those questions can later feed optional modules of an interview product without changing the core language.

---

## Bottom line

A fair reaction from a skeptical senior engineer:

> This will not replace my schema or my supervision tree — and it does not claim to.  
> It *is* a clear place for the business obligations long-lived systems keep losing.

That is the intended scope. Honesty about blindspots is part of making the methodology safe to promote and safe to use.
