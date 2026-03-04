# Agent Integration Examples

## OpenAI Agents (pseudo)
1. Before response, call `POST /api/v1/context` with `include_citations=true`.
2. Inject `context` + citation footnotes into model prompt.
3. After response, persist memory via `POST /api/v1/memories`.

## LangChain
- Use memorizer as a retriever sidecar: custom retriever calls `/api/v1/context`.
- Optional: use `/api/v1/profile` for user-state chain inputs.

## OpenClaw style
- In tool handlers, call `memorizer context <prompt>`.
- For governance workflows, use `memorizer export --namespace default`.
- Use `connector-sync <id>` from automation tasks.
