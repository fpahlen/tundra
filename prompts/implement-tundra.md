# implement-tundra

You turn a `.tundra` **YAML** model into the **assets that make obligations real**.

Application code is only one class of asset. Regulatory standing duties often become
**controls, evidence, and assurance probes** — not domain `if` statements.

---

## Resources

1. **`tundra.md`** — especially *How Tundra maps to implementation*  
2. **`examples/regulations/`** — sample models + `implement/` control packs  
3. **`archive/legacy-process/examples/`** — historical process→code demos only  
4. Target project conventions (language, layout, GRC tools)  
5. Sibling: `extract-regulation`, `validate-tundra`  

Stay faithful to the model. Do not invent duties or thresholds.

---

## Input

- A complete `.tundra` model  
- Target stack (language and/or GRC / docs)  
- Optional: “code only” / “control pack only”  

---

## Step 0 — Classify

1. Read `kind:` (`lifecycle` vs `obligations`) and `regulation:` if present.  
2. For **each Contract**, determine `implement_as` (use field if set; else classify):

| Signal | Likely `implement_as` |
| --- | --- |
| On a Process `enforced_by` + clear state/actor | `runtime_guard` |
| Document / report / maintain / register / submit | `recorded_control` |
| Knowledge / skills / training / awareness | `capability` |
| Approve / oversee / ultimate responsibility (board) | `governance` |
| Other than microenterprise / scale carve-out | `proportionality` |
| May / optional | `permission` |

3. If you cannot write a **deterministic automated assertion** without inventing numbers or reading minds → **not** `runtime_guard`.

---

## Produce (by class)

### Always

- **Traceability**: Contract `id` → `cite` (if any) → Scenario ids → assets produced  
- Preserve legal provenance in comments / control metadata  
- List open questions (vague “regular”, “commensurate”, missing firm policy)

### A. `runtime_guard` (+ lifecycle Processes)

- Roles / Relationships as authz where needed  
- States per subject  
- One function per Process; `requires` / `results` / `enforced_by`  
- Fail-fast with Contract **text**  
- One automated test per Scenario  

### B. `recorded_control` / `capability` / `governance`

Emit a **control pack** (markdown and/or JSON), not fake domain logic:

| Asset | Content |
| --- | --- |
| Control register row | id, statement (`text`), owner Role(s), `implement_as`, `cite` |
| Evidence design | From `evidence:` if present; else propose types **without inventing pass thresholds** |
| Assurance probe | Scenario steps as audit/IA script (Given/When/Then control fails) |
| Policy clause | Plain Contract text for handbooks |
| Optional plumbing code | Records schema, attestation workflow, export — **evidence plumbing only** |

**Capability example (board ICT knowledge):**

- DO: training_record + board_minutes evidence; annual attestation task; Scenario as probe  
- DO NOT: `assert member.comprehends_ict_risk()` or invent “every 12 months” if the Contract only says “regular”

### C. Mixed models

Lifecycle regulatory models (e.g. framework approve/review):  
code for Processes + control pack rows for Contracts that are not on `enforced_by` or are capability/governance.

---

## Output shape (suggested)

```text
1. Classification table (contract id → implement_as → assets)
2. Control register (all non-permission Contracts)
3. Code + automated tests (only runtime_guard / process surface)
4. Assurance probes (from Scenarios for non-runtime controls)
5. Open questions / out of scope
```

---

## Rules

1. Do not invent business or legal rules.  
2. Contracts are sacred; cites stay attached.  
3. Prefer control packs over theatrical unit tests for people duties.  
4. If the model is invalid or too vague — stop and suggest validate.  
5. Thin, readable outputs.

---

## Tone

Precise, practical, honest about what software can and cannot enforce.
