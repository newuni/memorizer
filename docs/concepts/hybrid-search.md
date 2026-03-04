# Hybrid Search

Hybrid mode merges candidates from:

- `memories` (agent/user facts)
- `document_chunks` (source knowledge)

## Controls

- `memory_weight` and `chunk_weight` adjust source priority.
- `threshold` removes low-score results.
- `filters` constrain metadata.
- `rerank` reorders by relevance.

Use hybrid for most chatbot/agent contexts.
