# memorizer

`memorizer` is a private-first, OSS-friendly memory service for AI agents.

## Tech stack
- FastAPI
- PostgreSQL + pgvector
- SQLAlchemy 2.x + Alembic
- Docker Compose

## MVP features
- Add a memory (`POST /api/v1/memories`)
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
