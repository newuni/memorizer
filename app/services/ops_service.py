from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime

from app.core.config import settings

_METRICS: dict[str, int] = defaultdict(int)
_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_DAILY_QUOTA: dict[tuple[str, str], tuple[str, int]] = {}


def inc_metric(name: str, value: int = 1) -> None:
    _METRICS[name] += value


def get_metrics_text() -> str:
    lines = ["# TYPE memorizer_counter counter"]
    for k, v in sorted(_METRICS.items()):
        lines.append(f"memorizer_counter{{name=\"{k}\"}} {v}")
    return "\n".join(lines) + "\n"


def enforce_rate_limit(key_id: str, per_minute: int | None = None) -> None:
    limit = int(per_minute or settings.rate_limit_per_minute)
    now = datetime.now(UTC).timestamp()
    q = _RATE_BUCKETS[key_id]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise ValueError("Rate limit exceeded")
    q.append(now)


def enforce_daily_quota(tenant_id: str, key_id: str, quota: int | None = None) -> None:
    maxq = int(quota or settings.default_daily_quota)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    k = (tenant_id, key_id)
    day, used = _DAILY_QUOTA.get(k, (today, 0))
    if day != today:
        used = 0
    if used >= maxq:
        raise ValueError("Daily quota exceeded")
    _DAILY_QUOTA[k] = (today, used + 1)
