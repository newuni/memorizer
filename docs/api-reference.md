# API Reference

Base path: `/api/v1`

Auth header: `X-API-Key: <key>`

## Memories

- `POST /memories`
- `POST /memories/batch`
- `POST /memories/batch/async`
- `DELETE /memories/{memory_id}`
- `GET /memories/search`

### Search query params

- `namespace` (string)
- `q` (string)
- `top_k` (int)
- `threshold` (float)
- `search_mode` (`hybrid` or basic mode)
- `rerank` (bool)
- `filters` (JSON string)
- `memory_weight` (float)
- `chunk_weight` (float)

## Context

- `POST /context`
  - body supports: `namespace`, `prompt`, `top_k`, `threshold`, `search_mode`, `rerank`, `memory_weight`, `chunk_weight`.

## Profile

- `GET /profile`
  - params: `namespace`, optional `q`, optional `top_k`.
  - returns `static`, `dynamic`, optional `search_results`.

## Documents

- `POST /documents`
- `GET /documents`
- `GET /documents/{doc_id}`
- `POST /documents/{doc_id}/process`
- `DELETE /documents/{doc_id}`

## Connectors

- `POST /connectors`
- `GET /connectors`
- `POST /connectors/{connector_id}/sync`

Providers currently: `github`, `web_crawler`.

## API Keys

- `GET /api-keys`
- `POST /api-keys`
- `DELETE /api-keys/{key_id}`

## Jobs

- `GET /jobs/{job_id}`

## Health

- `GET /health`
