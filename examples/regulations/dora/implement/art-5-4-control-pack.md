# Control pack: DORA Art. 5(4) — management body ICT knowledge

Derived from [`../dora-art-5-4-board-competence.tundra`](../dora-art-5-4-board-competence.tundra).  
This is what **implement** should produce for a `capability` Contract — not a fake “board understands ICT” unit test.

## Classification

| Contract id | implement_as | Why |
| --- | --- | --- |
| `mgmt-body-keeps-ict-knowledge-current` | `capability` (+ governance ownership) | Knowledge/skills/training; not a binary process guard |

## Control register

| Field | Value |
| --- | --- |
| **Control id** | `mgmt-body-keeps-ict-knowledge-current` |
| **Statement** | Members of the Management body of the Financial entity must keep up to date with knowledge and skills to understand and assess ICT risk and its impact on the operations of the Financial entity, including regular training commensurate with the ICT risk being managed. |
| **Owner (Tundra Role)** | Management body (map to firm role: e.g. Board / Company Secretary / CRO — **outside** the model) |
| **Instrument** | Regulation (EU) 2022/2554 (DORA) |
| **Cite** | Article 5, paragraph 4 |
| **Quote** | Members of the management body of the financial entity shall actively keep up to date with sufficient knowledge and skills to understand and assess ICT risk |
| **ELI** | https://eur-lex.europa.eu/eli/reg/2022/2554/oj |

## Evidence design

| type | description | Notes |
| --- | --- | --- |
| `training_record` | Completion records for board ICT-risk briefings / modules | Does **not** prove “understanding”; proves attendance/completion |
| `board_minutes` | Minute noting that training/briefing occurred | Common supervisory artefact |
| `skills_matrix` | Optional self- or facilitated assessment of ICT risk literacy | Firm-defined scale — **not** in the Tundra model |
| `attestation` | Periodic management-body attestation that members are kept up to date | Frequency: Contract says “regular” — firm policy must set the clock |

## Assurance probe (from Scenario)

Use as internal audit / second-line test script (manual or GRC), not as a unit test of cognition:

1. **Given** the Financial entity is in scope of the instrument  
2. **When** members of the Management body have no ongoing ICT risk training  
3. **Then** control `mgmt-body-keeps-ict-knowledge-current` **fails** (Contract broken)

Pass criteria for the probe are firm-defined (e.g. sample of board members with evidence in period P).  
**Do not invent P from the model** unless the Contract states a number.

## Optional software (evidence plumbing only)

If the firm wants systems support:

- Schema: person ↔ management-body membership ↔ training_record (date, topic, provider)  
- Workflow: recurring task “board ICT-risk training cycle”  
- Export: pack of records + minutes link for competent authority requests  

**Out of scope for codegen from this model alone:**

- Measuring actual understanding  
- Choosing the curriculum  
- Setting “every N months” without firm policy  

## Policy handbook clause

> Members of the management body shall actively keep up to date with sufficient knowledge and skills to understand and assess ICT risk and its impact on the operations of the financial entity, including through regular training commensurate with the ICT risk being managed.  
> *(DORA Art. 5(4))*

## Open questions (not answered by the model)

- What training content is “commensurate with the ICT risk being managed”?  
- What calendar implements “regular”?  
- Who in the org charts to Management body for evidence ownership?
