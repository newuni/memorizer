#!/usr/bin/env python3
"""memorizer CLI (HTTP client, no MCP needed)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_URL = os.getenv("MEMORIZER_URL", "http://localhost:8000")
DEFAULT_API_KEY = os.getenv("MEMORIZER_API_KEY", "dev-secret-change-me")


def _request(method: str, path: str, api_key: str, data: dict | None = None, base_url: str = DEFAULT_URL):
    url = f"{base_url.rstrip('/')}{path}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("X-API-Key", api_key)
    if body is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"detail": raw}
        return e.code, payload


def _print(payload: dict | list):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_health(args):
    status, payload = _request("GET", "/health", args.api_key, None, args.url)
    _print({"status_code": status, "data": payload})


def cmd_add(args):
    data = {
        "namespace": args.namespace,
        "content": args.content,
        "meta": json.loads(args.meta) if args.meta else {},
    }
    status, payload = _request("POST", "/api/v1/memories", args.api_key, data, args.url)
    _print({"status_code": status, "data": payload})


def cmd_search(args):
    path = f"/api/v1/memories/search?namespace={args.namespace}&q={urllib.parse.quote(args.query)}&top_k={args.top_k}"
    status, payload = _request("GET", path, args.api_key, None, args.url)
    _print({"status_code": status, "data": payload})


def cmd_context(args):
    data = {"namespace": args.namespace, "prompt": args.prompt, "top_k": args.top_k}
    status, payload = _request("POST", "/api/v1/context", args.api_key, data, args.url)
    _print({"status_code": status, "data": payload})


def cmd_batch_async(args):
    items = [{"namespace": args.namespace, "content": c, "meta": {"source": "cli"}} for c in args.items]
    status, payload = _request("POST", "/api/v1/memories/batch/async", args.api_key, {"items": items}, args.url)
    _print({"status_code": status, "data": payload})


def cmd_job(args):
    status, payload = _request("GET", f"/api/v1/jobs/{args.job_id}", args.api_key, None, args.url)
    _print({"status_code": status, "data": payload})


def cmd_keys_list(args):
    status, payload = _request("GET", "/api/v1/api-keys", args.api_key, None, args.url)
    _print({"status_code": status, "data": payload})


def cmd_keys_create(args):
    status, payload = _request("POST", "/api/v1/api-keys", args.api_key, {"name": args.name}, args.url)
    _print({"status_code": status, "data": payload})


def cmd_keys_revoke(args):
    status, payload = _request("DELETE", f"/api/v1/api-keys/{args.key_id}", args.api_key, None, args.url)
    _print({"status_code": status, "data": payload})


def build_parser():
    p = argparse.ArgumentParser(prog="memorizer", description="memorizer CLI (no MCP required)")
    p.add_argument("--url", default=DEFAULT_URL, help="Base URL, e.g. http://localhost:8000")
    p.add_argument("--api-key", default=DEFAULT_API_KEY, help="X-API-Key")

    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("health")
    s.set_defaults(func=cmd_health)

    s = sub.add_parser("add")
    s.add_argument("content")
    s.add_argument("--namespace", default="default")
    s.add_argument("--meta", default="{}", help="JSON string")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--namespace", default="default")
    s.add_argument("--top-k", type=int, default=5)
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("context")
    s.add_argument("prompt")
    s.add_argument("--namespace", default="default")
    s.add_argument("--top-k", type=int, default=5)
    s.set_defaults(func=cmd_context)

    s = sub.add_parser("batch-async")
    s.add_argument("items", nargs="+", help="Memory contents")
    s.add_argument("--namespace", default="default")
    s.set_defaults(func=cmd_batch_async)

    s = sub.add_parser("job")
    s.add_argument("job_id")
    s.set_defaults(func=cmd_job)

    s = sub.add_parser("keys-list")
    s.set_defaults(func=cmd_keys_list)

    s = sub.add_parser("keys-create")
    s.add_argument("name")
    s.set_defaults(func=cmd_keys_create)

    s = sub.add_parser("keys-revoke")
    s.add_argument("key_id")
    s.set_defaults(func=cmd_keys_revoke)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
