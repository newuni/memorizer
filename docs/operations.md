# Operations

## Environments

Recommended env vars:

- `DATABASE_URL`
- `REDIS_URL`
- `EMBEDDING_PROVIDER` (`local` or `gemini`)
- `LOCAL_EMBED_MODEL` / `GEMINI_API_KEY`
- `RERANK_ENABLED`, `RERANK_MODEL`, `RERANK_CANDIDATE_POOL`
- `HYBRID_MEMORY_WEIGHT`, `HYBRID_CHUNK_WEIGHT` (if configured through env mapping)

## Run stack

```bash
docker compose up -d --build
```

Services:
- `api`
- `worker`
- `db`
- `redis`

## Migrations

```bash
docker compose exec api alembic upgrade head
```

## Backups

- Dump PostgreSQL daily.
- Keep Redis as ephemeral queue state (not source of truth).
- Version `.env` templates, not secrets.

## Release cadence

Use SemVer and GitHub Releases (`RELEASING.md`).
