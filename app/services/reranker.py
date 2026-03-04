from __future__ import annotations

from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def _get_cross_encoder():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(settings.rerank_model, device="cpu")


def rerank(query: str, rows: list[dict], top_k: int) -> list[dict]:
    if not settings.rerank_enabled or not rows:
        return rows[:top_k]

    model = _get_cross_encoder()
    pairs = [(query, row["content"]) for row in rows]
    scores = model.predict(pairs)

    scored: list[dict] = []
    for row, rr_score in zip(rows, scores):
        hybrid = (0.65 * float(row.get("score", 0.0))) + (0.35 * float(rr_score))
        row2 = dict(row)
        row2["score"] = hybrid
        row2["rerank_score"] = float(rr_score)
        scored.append(row2)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
