# Intentional bad Contracts fixture

This model is **structurally valid** (passes schema, genesis, reachability) but has
**deliberately untestable Contracts**. Use it to exercise vagueness detection and
extract/validate refusal of fuzzy rules.

**Do not** copy its Contract style into real models.

```bash
# Included in --all with expected warnings (vagueness), not hard errors
python3 tools/check_tundra.py examples/bad-contracts/

# Assert at least one vagueness warning (CI)
python3 tools/check_tundra.py examples/bad-contracts/ 2>&1 | grep -q 'comparative or vague'
```

## Defects (intentional)

- “high relative to income” / “low relative to income” without a number
- “fall between” automatic approval and decline without thresholds

Structure (BankID → credit check → decision with `outcomes`) is intentionally *good*
so the only failures are Contract quality.

## Files

| File | Description |
| --- | --- |
| `loan-application-entry.tundra` | Bad-contracts specimen |
