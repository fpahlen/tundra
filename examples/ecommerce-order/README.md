# Example: E-commerce order lifecycle

Model-only example of cart → order → payment → shipment.

## Files

| File | Description |
|------|-------------|
| `ecommerce-order.tundra` | Canonical Tundra model (YAML) |

## Illustrates

- Aggregational decorators (`contains`, `quantity`)
- Cancel window via `before: Shipped`
- Multi-role flow: Customer, Merchant, Payment Provider

## See also

- Language definition: [`../../tundra.md`](../../tundra.md)
- Catalog: [`../README.md`](../README.md)
