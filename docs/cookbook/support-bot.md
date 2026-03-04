# Cookbook: Support Bot

## Goal

Support bot that remembers user history and troubleshooting context.

## Pattern

- Ingest knowledge base docs as documents.
- On each message, call hybrid `/context`.
- Use metadata filters for product/version.
- Persist resolved outcomes as memories.

## Useful metadata

- `product`
- `version`
- `severity`
- `team`
