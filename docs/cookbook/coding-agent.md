# Cookbook: Coding Agent

## Goal

Give a coding agent durable memory across sessions.

## Pattern

1. Before answering, call `/api/v1/context` with current user prompt.
2. Inject returned context into system prompt.
3. After meaningful events, store memory via `/api/v1/memories`.

## Example memories

- "User prefers concise responses"
- "Project uses Docker and Caddy"
- "Repository release flow uses GitHub Releases"
