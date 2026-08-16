# implement-tundra (skill reference)

Turn a `.tundra` model into **assets that realize obligations** — not always application code.

Prefer project `tundra.md` (*How Tundra maps to implementation*) when present.

---

## Branch on model kind

| `kind` | Default deliverable |
| --- | --- |
| `lifecycle` | Domain code + automated Scenario tests for Processes / `enforced_by` |
| `obligations` | **Control pack** (register, evidence, assurance probes); code only for evidence plumbing |

Regulatory models with both Processes and standing duties → **both**.

---

## Classify each Contract (`implement_as`)

Use the field if set. Else:

- `enforced_by` on a Process → `runtime_guard`  
- training / knowledge / skills → `capability`  
- approve / oversee / board responsibility → `governance`  
- document / report / maintain register → `recorded_control`  
- carve-outs / microenterprise → `proportionality`  
- may / optional → `permission`  

**Rule:** if you cannot assert the duty deterministically without inventing thresholds or mind-reading, do **not** emit a fake domain guard — emit control + evidence + Scenario as **assurance probe**.

---

## Produce

1. Classification table  
2. Control register rows (id, text, cite, owner Role, implement_as, evidence)  
3. Code + unit/integration tests **only** for `runtime_guard` / Process surface  
4. Assurance probes from Scenarios for capability/governance/recorded controls  
5. Open questions (unspecified frequency, “commensurate”, firm policy gaps)

Preserve `regulation` / `cite` on every control and in code comments where relevant.

---

## Anti-patterns

- `assert board_has_knowledge()` for DORA-style training duties  
- Inventing “every 12 months” when the Contract says “regular”  
- Ignoring legal cites in generated assets  
- Generating only code for a pure `kind: obligations` model  

---

## Tone

Faithful, practical, honest about people/process controls vs software.
