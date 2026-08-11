# Example: Booking and reservation

Canonical model with temporal and capacity decorators, plus a thin Elixir implementation.

## Files

| File | Description |
|------|-------------|
| `booking-reservation.tundra` | Canonical Tundra model (YAML) |
| `booking.ex` | Implementation — States as atoms, one function per Process |
| `booking_scenarios.exs` | Executable Scenarios from the model |

## Run

```bash
elixir booking_scenarios.exs
```

## Mapping

| Tundra | Elixir |
|--------|--------|
| States | Atoms (`:pending`, `:confirmed`, …) |
| Processes | Functions returning `{:ok, state}` or `{:error, contract_text}` |
| Contracts | Checked explicitly; error message is the Contract text |
| Temporal decorators | Guards on `DateTime` arguments (`@before`, `@after`, `@within`) |
| Capacity | Field on the time-slot map |

## See also

- Language definition: [`../../tundra.md`](../../tundra.md)
- Catalog: [`../README.md`](../README.md)
