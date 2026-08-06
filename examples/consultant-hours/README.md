# Example: Consultant hours to client invoice

This folder contains a complete Tundra model and two thin implementations of its happy-path Scenario.

## Files

| File | Description |
|------|-------------|
| `consultant-hours-invoice.tundra` | The Tundra model (source of truth) |
| `happy_path.py` | Python implementation of the happy-path Scenario |
| `happy_path.c` | ANSI C implementation of the same Scenario |

## Run the examples

**Python**
```bash
python happy_path.py
```

**C**
```bash
cc -o happy_path happy_path.c
./happy_path
```

Both programs walk the same path:

1. Register Hours → Hours are in Draft  
2. Submit Hours → Hours are Submitted  
3. Create Invoice → Invoice is Open  
4. Approve Invoice → Invoice is Approved  

and print the state after each step. Contract violations fail fast with a clear message.
