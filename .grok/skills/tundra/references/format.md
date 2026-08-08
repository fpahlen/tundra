# Tundra format (skill reference)

Plain-English models for **who may do what**, under which conditions, with living examples.  
Files use the suffix `.tundra`.

## Five concepts

| Concept | Meaning |
|---------|---------|
| **Roles** | Named actors (a person can hold several) |
| **Contracts** | Authoritative, testable rules — single source of truth |
| **States** | Meaningful situations of a **named subject** (“Hours are in Draft”) |
| **Processes** | Transformations with **Actor**, **Requires**, **Results** |
| **Scenarios** | End-to-end examples → tests |

## Exact output format

```text
Tundra: <short name>

  Roles:
    - <Role name>

  Contracts:
    - <testable rule>

  States:
    - <Subject is Some state>

  Processes:
    - <Process name>
        Actor: <Role or System>
        Requires: <State or short condition>
        Results: <State or short outcome>

  Scenario: <happy path name>
    Given ...
    When the <Role> ...
    Then ...

  Scenario: <error path name>
    Given ...
    When the <Role> tries to ...
    Then ...
    And the contract "..." is broken
```

## Scenario vocabulary

| Situation | Phrase |
|-----------|--------|
| Forbidden action | `is broken` |
| Automatic rule fires correctly | `is applied` |

## Key rules

1. Never invent important knowledge — ask instead.  
2. Prefer thin models.  
3. Contracts must be testable (no “too high”, “reasonable”, “low risk”, “falls between”).  
4. Roles are first-class.  
5. Every State names its subject.  
6. Processes declare Actor, Requires, Results.  
7. Reuse Role/Contract names across models; no silent synonyms.  
8. Scenarios demonstrate Contracts (happy path + important errors).

## Map to code

| Tundra | Code |
|--------|------|
| Role | Actor param / enum on process functions |
| Contract | Fail-fast check; message quotes Contract text |
| State | Enum **per subject** (not one mega-enum) |
| Process | One function; guard Actor + Requires |
| Scenario | Executable test |

## Scope (do not force into Contracts)

Not a data model, NFR catalog, threat model, or full test strategy.  
Pair with schema, audit logs, retries, money golden-tests, etc. when those risks matter.

Clean example: `example.tundra` in this folder.
