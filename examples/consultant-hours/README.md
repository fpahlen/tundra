# Example: Consultant hours to client invoice

Canonical YAML model plus thin reference implementations (happy path and error paths).

## Files

| File | Description |
| --- | --- |
| `consultant-hours-invoice.tundra` | Canonical Tundra model (YAML; source of truth) |
| `demo.py` | Python: Roles, per-subject state, Contracts, three Scenarios |
| `demo.c` | ANSI C twin of the same Scenarios |

## What this demonstrates

- **Roles** are first-class (actor parameter on every Process)
- **Relationships** (Owner / Creator / Recipient)
- **Hours** and **Invoice** are separate state machines
- **Contracts** fail fast with the Contract text from the model
- **Error Scenarios** show `contract … is broken` behaviour in code

## Run

**Python**

```bash
python3 demo.py              # all scenarios
python3 demo.py happy
python3 demo.py error-edit
python3 demo.py error-invoice

```

**C**

```bash
cc -o demo demo.c
./demo                      # all scenarios
./demo happy
./demo error-edit
./demo error-invoice

```

## Scenarios

1. **Happy path** — Register → Submit → Create Invoice → Approve  
2. **Error: edit after submit** — Consultant cannot edit Submitted hours  
3. **Error: wrong role creates invoice** — Only the Manager may create an invoice  

## See also

- Language definition: [`../../tundra.md`](../../tundra.md)
- Catalog: [`../README.md`](../README.md)
