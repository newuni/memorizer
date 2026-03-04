# Admin Runbook

## Admin access

Use `X-Admin-Token` for all `/api/v1/admin/*` endpoints.

```bash
export MEMORIZER_URL=http://localhost:8000
export MEMORIZER_ADMIN_TOKEN=dev-admin-owner-token
```

Role capabilities:
- `owner`: global read/write, tenant create, hard delete.
- `admin`: read/write inside scoped tenant (or explicit tenant if unscoped).
- `viewer`: read-only.

## Tenant + namespace operations

List tenants:

```bash
curl -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" \
  "$MEMORIZER_URL/api/v1/admin/tenants"
```

Create tenant:

```bash
curl -X POST -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme","name":"Acme","daily_quota":10000,"rate_limit_per_minute":240,"retention_days":30,"purge_after_forget_days":7}' \
  "$MEMORIZER_URL/api/v1/admin/tenants"
```

Create namespace:

```bash
curl -X POST -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme","name":"support","retention_days":14}' \
  "$MEMORIZER_URL/api/v1/admin/namespaces"
```

## API keys + quotas

Create tenant API key with quotas:

```bash
curl -X POST -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme","name":"support-bot","rate_limit_per_minute":60,"daily_quota":20000}' \
  "$MEMORIZER_URL/api/v1/admin/api-keys"
```

Patch quotas:

```bash
curl -X PATCH -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme","rate_limit_per_minute":120,"daily_quota":40000}' \
  "$MEMORIZER_URL/api/v1/admin/api-keys/<key_id>"
```

## Queue health + events

Queue health:

```bash
curl -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" \
  "$MEMORIZER_URL/api/v1/admin/observability/queue-health"
```

Event feed:

```bash
curl -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" \
  "$MEMORIZER_URL/api/v1/admin/observability/events?tenant_id=acme&limit=50"
```

## Export and delete/forget workflows

Paged export:

```bash
curl -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" \
  "$MEMORIZER_URL/api/v1/admin/tenants/acme/export?page_size=100&cursor=0"
```

Streaming export (NDJSON):

```bash
curl -N -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" \
  "$MEMORIZER_URL/api/v1/admin/tenants/acme/export/stream"
```

Dry-run forget:

```bash
curl -X POST -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"dry_run":true,"hard_delete":false}' \
  "$MEMORIZER_URL/api/v1/admin/tenants/acme/forget"
```

Hard delete (`owner` only):

```bash
curl -X POST -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"dry_run":false,"hard_delete":true}' \
  "$MEMORIZER_URL/api/v1/admin/tenants/acme/forget"
```

## Retention policies

Update tenant policy:

```bash
curl -X PUT -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"retention_days":30,"purge_after_forget_days":7}' \
  "$MEMORIZER_URL/api/v1/admin/tenants/acme/retention"
```

Run retention enforcement task:

```bash
curl -X POST -H "X-Admin-Token: $MEMORIZER_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme","dry_run":true}' \
  "$MEMORIZER_URL/api/v1/admin/governance/retention/enforce"
```
