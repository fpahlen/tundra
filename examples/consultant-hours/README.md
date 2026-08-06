# Example: Consultant hours to client invoice

Thin reference implementations of the canonical Tundra model.

**Source of truth:** [`../../models/consultant-hours-invoice.tundra`](../../models/consultant-hours-invoice.tundra)

## Files

| File | Description |
|------|-------------|
| `demo.py` | Python: Roles, per-subject state, Contracts, three Scenarios |
| `demo.c` | ANSI C twin of the same Scenarios |

Older `happy_path.py` / `happy_path.c` names are replaced by `demo.py` / `demo.c`.

## What this demonstrates

- **Roles** are first-class (actor parameter on every Process)
- **Hours** and **Invoice** are separate state machines (subject named in the model)
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
