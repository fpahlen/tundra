# Control pack: MiFID II Art. 25(2) — suitability information and recommendation

Derived from [`../mifid-ii-art-25-suitability.tundra`](../mifid-ii-art-25-suitability.tundra).  
This is what **implement** should produce for suitability **recorded_control** Contracts — not a fake “product is suitable” unit test of investor welfare.

## Classification

| Contract id | implement_as | Why |
| --- | --- | --- |
| `obtain-suitability-info` | `recorded_control` | Collect and retain fact-find / KYC inputs |
| `recommend-only-if-suitable` | `recorded_control` | Decision record that recommendation matches assessed suitability |

Staff competence (`staff-knowledge-and-competence`) is a separate **capability** control (training/register), not expanded in this pack.

## Control register

### Control A — obtain suitability information

| Field | Value |
| --- | --- |
| **Control id** | `obtain-suitability-info` |
| **Statement** | When providing investment advice or portfolio management, the Investment firm must obtain the necessary information on the Client's or Potential client's knowledge and experience in the investment field relevant to the product or service, financial situation including ability to bear losses, and investment objectives including risk tolerance. |
| **Owner (Tundra Role)** | Investment firm (map to: advice desk / client onboarding / portfolio management — **outside** the model) |
| **Instrument** | Directive 2014/65/EU (MiFID II) |
| **Cite** | Article 25, paragraph 2 |
| **Quote** | shall obtain the necessary information regarding the client’s or potential client’s knowledge and experience in the investment field relevant to the specific type of product or service, that person’s financial situation including his ability to bear losses, and his investment objectives including his risk tolerance |
| **ELI** | https://eur-lex.europa.eu/eli/dir/2014/65/oj |

### Control B — recommend only if suitable

| Field | Value |
| --- | --- |
| **Control id** | `recommend-only-if-suitable` |
| **Statement** | When providing investment advice or portfolio management, the Investment firm may recommend (or decide for portfolio management) only investment services and financial instruments that are suitable for the Client or Potential client, in particular in accordance with that person's risk tolerance and ability to bear losses. |
| **Owner (Tundra Role)** | Investment firm (map to: adviser / PM mandate system) |
| **Instrument** | Directive 2014/65/EU (MiFID II) |
| **Cite** | Article 25, paragraph 2 |
| **Quote** | recommend to the client or potential client the investment services and financial instruments that are suitable for him and, in particular, are in accordance with his risk tolerance and ability to bear losses |
| **ELI** | https://eur-lex.europa.eu/eli/dir/2014/65/oj |

## Evidence design

| type | description | Notes |
| --- | --- | --- |
| `other` (≥40-char description) | Suitability questionnaire / fact-find | Captures knowledge, experience, finances, objectives, risk tolerance — **not** proof the product is “good” |
| `register` | Client suitability profile | Durable client record |
| `other` | Suitability assessment decision | Links product/service to assessed profile |
| `log_export` | Block / allow trail | Shows recommendation blocked when suitability fails |

Use controlled `evidence.type` values; prefer `other` with a real description for questionnaire/decision artefacts (no dedicated enum yet).

## Assurance probes (from Scenarios)

Internal audit / second-line scripts (manual or GRC), not unit tests of “correct advice”:

1. **Given** the firm provides investment advice or portfolio management  
   **When** information on knowledge, experience, financial situation (incl. loss-bearing), and objectives (incl. risk tolerance) has not been obtained  
   **Then** control `obtain-suitability-info` **fails**

2. **Given** the firm provides investment advice  
   **When** a financial instrument is recommended that is not suitable given risk tolerance and ability to bear losses  
   **Then** control `recommend-only-if-suitable` **fails**

Pass criteria (sampling, recency, completeness) are firm-defined.  
**Do not invent scoring models from the Tundra text alone.**

## Optional software (evidence plumbing only)

- Schema: client ↔ suitability profile ↔ assessment decision ↔ recommendation/order  
- Workflow: advice journey blocked until profile complete and decision recorded  
- Export: pack for competent authority requests  

**Out of scope for codegen from this model alone:**

- Designing the questionnaire content (Level 2 / ESMA / firm methodology)  
- Deciding what is “suitable” for a given client  
- Sustainability preferences and other post-2014 refinements not in this Level 1 excerpt  

## Policy handbook clause

> When providing investment advice or portfolio management the investment firm shall obtain the necessary information regarding the client’s or potential client’s knowledge and experience … financial situation including his ability to bear losses, and his investment objectives including his risk tolerance so as to enable the investment firm to recommend … the investment services and financial instruments that are suitable for him …  
> *(MiFID II Art. 25(2))*

## Open questions (not answered by the model)

- What questionnaire fields and refresh cycle does the firm use?  
- How is “ability to bear losses” operationalised?  
- Who owns the control in the three lines of defence?
