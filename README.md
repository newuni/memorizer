# memorizer

`memorizer` is a private-first, OSS-friendly memory service for AI agents.

## Tech stack
- FastAPI
- PostgreSQL + pgvector
- SQLAlchemy 2.x + Alembic
- Docker Compose

## MVP features
- API key auth + tenant isolation (`X-API-Key`)
- Add one memory (`POST /api/v1/memories`)
- Add many memories (`POST /api/v1/memories/batch`)
- Search memories semantically (`GET /api/v1/memories/search`)
- Build LLM context (`POST /api/v1/context`)
- Delete memory (`DELETE /api/v1/memories/{id}`)
- Health check (`GET /health`)

## Quick start

```bash
docker compose up --build
```

API: `http://localhost:8000`
Docs: `http://localhost:8000/docs`

## Environment
Copy `.env.example` to `.env` if needed.

### Embeddings providers
By default, memorizer uses a **local CPU model**:

```env
EMBEDDING_PROVIDER=local
LOCAL_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

To switch to **Gemini embeddings** at any time, set:

```env
EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_EMBED_MODEL=models/text-embedding-004
```

> Keep `EMBEDDING_DIM=384` unless you also migrate the DB vector column.

### API key bootstrap (dev)
On startup, the API creates/ensures one bootstrap key from env:

```env
BOOTSTRAP_TENANT_ID=default
BOOTSTRAP_API_KEY=dev-secret-change-me
```

Use it in requests:

```bash
curl -H "X-API-Key: dev-secret-change-me" \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","content":"Unai likes OSS tools","meta":{"source":"chat"}}' \
  http://localhost:8000/api/v1/memories
```

Create extra keys manually:

```bash
docker compose exec api python scripts/create_api_key.py
```
