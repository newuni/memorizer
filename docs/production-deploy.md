# Production Deploy (Docker + Caddy)

## Overview

Deploy memorizer behind Caddy with TLS on `newuni.org`.

## 1) Compose services

Run:

```bash
docker compose up -d --build
```

Ensure these are healthy:
- `memorizer-api`
- `memorizer-worker`
- `memorizer-db`
- `memorizer-redis`

## 2) Caddy reverse proxy

Example Caddy snippet:

```caddy
memory.newuni.org {
  reverse_proxy 127.0.0.1:8000
}
```

If you use path routing:

```caddy
newuni.org {
  handle_path /memory/* {
    reverse_proxy 127.0.0.1:8000
  }
}
```

## 3) Hardening checklist

- Rotate bootstrap dev key for production.
- Use strong per-tenant API keys.
- Restrict DB/Redis to private network.
- Keep backups of PostgreSQL.
- Monitor API/worker logs.

## 4) Upgrade flow

1. Pull latest code.
2. Apply migrations.
3. Restart API + worker.
4. Run health + smoke calls.

## 5) Smoke test

```bash
curl https://memory.newuni.org/health
```
