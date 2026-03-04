# Security

## Authentication

- API uses `X-API-Key`.
- Keys are hashed at rest (`sha256`).
- Keys can be listed/created/revoked per tenant.

## Tenant isolation

All read/write operations are constrained by `tenant_id` derived from the API key.

## Secret handling

- Keep real keys in environment variables.
- Do not commit secrets.
- Rotate production keys periodically.

## Production recommendations

- Put API behind TLS reverse proxy.
- Restrict DB/Redis network exposure.
- Enable logs/monitoring and alerting.

For vuln reporting, see `SECURITY.md` at repository root.
