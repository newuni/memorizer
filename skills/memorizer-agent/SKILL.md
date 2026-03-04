---
name: memorizer-agent
description: Use memorizer as long-term memory for agents without MCP by calling the HTTP API directly (or via scripts/memorizer CLI).
---

# memorizer-agent skill

Use this when an agent needs a practical memory loop:
1. Save durable facts/preferences after interactions.
2. Retrieve relevant context before answering.
3. Inject context into the LLM prompt.

## Preferred interfaces
- **CLI**: `scripts/memorizer ...` (fastest, no MCP)
- **HTTP API**: direct calls to `/api/v1/*`

## Environment
- `MEMORIZER_URL` (default `http://localhost:8000`)
- `MEMORIZER_API_KEY` (default `dev-secret-change-me`)

## Typical commands
```bash
# Save a memory
scripts/memorizer add "User prefers concise Spanish replies" --namespace default --meta '{"type":"preference"}'

# Get context for current prompt
scripts/memorizer context "¿Cómo lo desplegamos?" --namespace default --top-k 5

# Search explicitly
scripts/memorizer search "docker caddy" --namespace default --top-k 5
```

## Recommended agent pattern
- On every relevant turn, store 0-2 compact memories.
- Before composing a response, call `context` with the user prompt.
- Include returned context only if relevant (avoid prompt bloat).
- For bulk imports, use `batch-async` and poll `job`.

## API key lifecycle
```bash
scripts/memorizer keys-list
scripts/memorizer keys-create agent-prod
scripts/memorizer keys-revoke <key_id>
```
