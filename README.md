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
