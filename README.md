# memorizer

[![CI](https://github.com/newuni/memorizer/actions/workflows/ci.yml/badge.svg)](https://github.com/newuni/memorizer/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/newuni/memorizer)](https://github.com/newuni/memorizer/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

`memorizer` is a private-first, OSS-friendly memory service for AI agents.

## Tech stack
- FastAPI
- PostgreSQL + pgvector
- Redis + Celery workers
- SQLAlchemy 2.x + Alembic
- Docker Compose

## Features (v0.4-dev)
- API key auth + tenant isolation (`X-API-Key`)
- Add one memory (`POST /api/v1/memories`)
- Add many memories sync (`POST /api/v1/memories/batch`)
- Add many memories async (`POST /api/v1/memories/batch/async`)
- Track ingestion jobs (`GET /api/v1/jobs/{job_id}`)
- Advanced search: hybrid mode, threshold, filters, rerank toggle (`GET /api/v1/memories/search`)
- Build LLM context (`POST /api/v1/context`)
- User profile endpoint (`GET /api/v1/profile`)
- Documents pipeline (`/api/v1/documents*`) with async chunk processing
- Connectors (github/web_crawler) (`/api/v1/connectors*`)
- API key management (list/create/revoke)
- Health check (`GET /health`)

## Public quickstart

```bash
git clone https://github.com/newuni/memorizer.git
cd memorizer
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`

## Documentation
- Main docs index: `docs/README.md`
- API reference: `docs/api-reference.md`
- API examples: `docs/api-examples.md`
- Architecture + diagrams: `docs/architecture.md`, `docs/architecture-diagrams.md`
- Production deploy (Docker + Caddy): `docs/production-deploy.md`
- Concepts + cookbooks: `docs/concepts/*`, `docs/cookbook/*`
- LLM-friendly docs: `docs/llms.txt`, `docs/llms-full.txt`

## Project hygiene
- Releases: `RELEASING.md`
- Changelog: `CHANGELOG.md`
- Contributing: `CONTRIBUTING.md`
- Security policy: `SECURITY.md`
- License: `LICENSE`

## Agent skill + CLI (no MCP)
This repo includes a dedicated skill and CLI so agents can use memorizer directly over HTTP.

- Skill: `skills/memorizer-agent/SKILL.md`
- CLI (repo-local): `scripts/memorizer`
- CLI (global with pipx): `memorizer`

### Install with pipx

From local clone:
```bash
cd /path/to/memorizer
pipx install .
```

From GitHub:
```bash
pipx install git+https://github.com/newuni/memorizer.git
```

Upgrade later:
```bash
pipx upgrade memorizer-cli
```

### Quick usage

```bash
# optional env vars
export MEMORIZER_URL=http://localhost:8000
export MEMORIZER_API_KEY=dev-secret-change-me

# save memory
memorizer add "User prefers concise Spanish replies" --meta '{"type":"preference"}'

# retrieve context for current prompt
memorizer context "¿Cómo lo desplegamos?" --top-k 5

# create/revoke api keys
memorizer keys-create agent-prod
memorizer keys-revoke <key_id>
```

## Embeddings providers
By default, memorizer uses a **local CPU model**:

```env
EMBEDDING_PROVIDER=local
LOCAL_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

To switch to **Gemini embeddings** at any time:

```env
EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_EMBED_MODEL=models/text-embedding-004
```

> Keep `EMBEDDING_DIM=384` unless you migrate the DB vector column.

## Reranking
Optional cross-encoder rerank (CPU):

```env
RERANK_ENABLED=true
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANK_CANDIDATE_POOL=25
```

## Auth bootstrap (dev)
On startup, the API creates/ensures a bootstrap API key:

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

## API keys management
List keys:

```bash
curl -H "X-API-Key: dev-secret-change-me" http://localhost:8000/api/v1/api-keys
```

Create key:

```bash
curl -X POST -H "X-API-Key: dev-secret-change-me" -H "Content-Type: application/json" \
  -d '{"name":"agent-prod"}' http://localhost:8000/api/v1/api-keys
```

Revoke key:

```bash
curl -X DELETE -H "X-API-Key: dev-secret-change-me" \
  http://localhost:8000/api/v1/api-keys/<key_id>
```

## Async batch ingestion
```bash
curl -X POST -H "X-API-Key: dev-secret-change-me" -H "Content-Type: application/json" \
  -d '{"items":[{"namespace":"default","content":"A"},{"namespace":"default","content":"B"}]}' \
  http://localhost:8000/api/v1/memories/batch/async
```

Then poll job status:

```bash
curl -H "X-API-Key: dev-secret-change-me" http://localhost:8000/api/v1/jobs/<job_id>
```

## How an agent uses memorizer
A typical agent flow is:
1. Save relevant facts/events as memories.
2. Before answering a user, fetch context from memorizer.
3. Inject retrieved context into the model prompt.

### Minimal Python example (agent-side)
```python
import requests

MEMORIZER_URL = "http://localhost:8000"
API_KEY = "dev-secret-change-me"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def remember(text: str, namespace: str = "default", meta: dict | None = None):
    payload = {
        "namespace": namespace,
        "content": text,
        "meta": meta or {"source": "agent"},
    }
    requests.post(f"{MEMORIZER_URL}/api/v1/memories", headers=HEADERS, json=payload, timeout=10).raise_for_status()


def build_context(user_prompt: str, namespace: str = "default", top_k: int = 5) -> str:
    payload = {"namespace": namespace, "prompt": user_prompt, "top_k": top_k}
    r = requests.post(f"{MEMORIZER_URL}/api/v1/context", headers=HEADERS, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()["context"]


# 1) Store memory after an interaction
remember("User prefers concise answers in Spanish", meta={"type": "preference"})

# 2) Retrieve context before generating a reply
user_prompt = "¿Qué me recomiendas para desplegar esto?"
ctx = build_context(user_prompt)

# 3) Inject context into your LLM prompt
final_prompt = f"""
Use this long-term context if relevant:
{ctx}

User request:
{user_prompt}
"""
print(final_prompt)
```

### Same idea with curl
```bash
# Save memory
curl -X POST -H "X-API-Key: dev-secret-change-me" -H "Content-Type: application/json" \
  -d '{"namespace":"default","content":"User likes Docker-first deploys","meta":{"source":"agent"}}' \
  http://localhost:8000/api/v1/memories

# Build context for current user prompt
curl -X POST -H "X-API-Key: dev-secret-change-me" -H "Content-Type: application/json" \
  -d '{"namespace":"default","prompt":"How should I deploy this?","top_k":5}' \
  http://localhost:8000/api/v1/context
```
