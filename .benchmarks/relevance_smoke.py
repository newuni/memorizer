"""Small relevance benchmark scaffold.
Run: python .benchmarks/relevance_smoke.py http://localhost:8000 dev-secret-change-me
"""

import json
import sys
import urllib.request

URL = sys.argv[1]
KEY = sys.argv[2]

CASES = [
    {"prompt": "deployment", "expect": "deploy"},
    {"prompt": "database", "expect": "postgres"},
]


def call(prompt: str):
    req = urllib.request.Request(
        f"{URL}/api/v1/context",
        data=json.dumps({"namespace": "default", "prompt": prompt, "top_k": 3}).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": KEY},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


hits = 0
for c in CASES:
    out = call(c["prompt"])
    text = out.get("context", "").lower()
    ok = c["expect"] in text
    hits += int(ok)
    print(c["prompt"], "OK" if ok else "MISS")

print(f"hit_rate={hits/len(CASES):.2f}")
