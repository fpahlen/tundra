# Example: Marketplace listing and sale

Model-only example of listing, offers, sale, and platform moderation.

## Files

| File | Description |
|------|-------------|
| `marketplace-listing.tundra` | Canonical Tundra model |

## Illustrates

- Multi-party Relationships (Owner, Offeror, Party to Sale, Moderator)
- Temporal expiry on awaiting payment (`@expires-in 48 hours`)
- Platform administrator suspend rule as a plain Contract (no embedded code)

## See also

- Language definition: [`../../tundra.md`](../../tundra.md)
- Catalog: [`../README.md`](../README.md)
