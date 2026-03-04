# Memorizer Blueprint (v0.3-dev)

## 1. Objective
Memory API for AI agents with multi-tenant isolation, semantic retrieval, reranking, and sync/async ingestion.

## 2. Architecture
- **API layer**: FastAPI
- **Storage**:
  - PostgreSQL metadata + governance tables
  - pgvector in `memories.embedding`
- **Queue/Workers**:
  - Redis as broker/backend
  - Celery workers for async batch ingestion
- **Embeddings abstraction**:
  - `LocalCPUEmbedder` (SentenceTransformers)
  - `GeminiEmbedder` switchable from `.env`

## 3. Domain model
- `memories`
  - `id`, `tenant_id`, `namespace`, `content`, `meta`, `embedding`, timestamps
- `api_keys`
  - `id`, `tenant_id`, `name`, `key_hash`, `is_active`, `created_at`
- `ingestion_jobs`
  - `id`, `tenant_id`, `status`, `total_items`, `processed_items`, `error`, timestamps

## 4. Retrieval strategy
1. Vector similarity search in pgvector (`embedding <=> query_embedding`)
2. Candidate pool configurable (`RERANK_CANDIDATE_POOL`)
3. Optional cross-encoder rerank (`RERANK_ENABLED=true`)
4. Final top-K returned to clients and `/context`

## 5. API contract
- `POST /api/v1/memories`
- `POST /api/v1/memories/batch`
- `POST /api/v1/memories/batch/async`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/memories/search`
- `POST /api/v1/context`
- `DELETE /api/v1/memories/{memory_id}`
- `GET /api/v1/api-keys`
- `POST /api/v1/api-keys`
- `DELETE /api/v1/api-keys/{key_id}`
- `GET /health`

## 6. Security
- Mandatory `X-API-Key`
- Key hashed at rest (`sha256`)
- Tenant isolation enforced in every query
- Bootstrap dev key from env for local onboarding

## 7. Roadmap
- **v0.3** (current): API keys mgmt, async ingestion, rerank, provider switching
- **v0.4**: HNSW/IVFFlat indexes tuning + metadata filters
- **v0.5**: connectors (web/slack/notion), fact extraction, memory compaction
- **v0.6**: audit logs, quotas/rate limits, RBAC
