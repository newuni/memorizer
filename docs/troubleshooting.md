# Troubleshooting

## API returns 401

- Verify `X-API-Key` header.
- Ensure key is active (`GET /api/v1/api-keys`).

## Search returns poor results

- Increase `top_k` and enable rerank.
- Tune `memory_weight` / `chunk_weight`.
- Add richer metadata and use filters.

## Document stuck in processing

- Check worker container logs.
- Validate source URL reachability for url docs.

## High latency

- Rerank adds extra cost.
- Reduce candidate pool.
- Scale workers.

## Embedding errors

- Confirm provider config (`EMBEDDING_PROVIDER`).
- For Gemini, validate `GEMINI_API_KEY` and model.
