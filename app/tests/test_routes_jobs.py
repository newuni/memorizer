from types import SimpleNamespace
from uuid import uuid4

from app.api import routes


def test_async_batch_enqueues_job(client, monkeypatch):
    jid = uuid4()

    monkeypatch.setattr(
        routes,
        "create_job",
        lambda db, tenant_id, total_items: SimpleNamespace(
            id=jid,
            status="queued",
            total_items=total_items,
            processed_items=0,
            error=None,
        ),
    )

    called = {"args": None}

    class _DelayStub:
        @staticmethod
        def delay(job_id, tenant_id, items):
            called["args"] = (job_id, tenant_id, items)

    monkeypatch.setattr(routes, "ingest_batch_task", _DelayStub)

    resp = client.post(
        "/api/v1/memories/batch/async",
        json={"items": [{"namespace": "default", "content": "A"}, {"namespace": "default", "content": "B"}]},
    )

    assert resp.status_code == 200
    assert resp.json()["id"] == str(jid)
    assert called["args"][0] == str(jid)
    assert called["args"][1] == "t1"
    assert len(called["args"][2]) == 2


def test_get_job_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(routes, "get_job", lambda db, tenant_id, job_id: None)

    resp = client.get(f"/api/v1/jobs/{uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Job not found"


def test_get_job_ok(client, monkeypatch):
    jid = uuid4()
    monkeypatch.setattr(
        routes,
        "get_job",
        lambda db, tenant_id, job_id: SimpleNamespace(
            id=jid,
            status="done",
            total_items=10,
            processed_items=10,
            error=None,
        ),
    )

    resp = client.get(f"/api/v1/jobs/{jid}")

    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
    assert resp.json()["processed_items"] == 10
