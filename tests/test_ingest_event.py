from __future__ import annotations

from datetime import datetime
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from api.fastapi_app import app, engine, event_table, metadata


def reset_db() -> None:
    metadata.drop_all(engine)
    metadata.create_all(engine)


def test_ingest_event_success():
    reset_db()
    client = TestClient(app)
    evt = {
        "event_id": "evt1",
        "ts": datetime.utcnow().isoformat(),
        "src": "unit-test",
        "content": {"msg": "hi"},
    }
    resp = client.post("/ingest/event", json=evt, headers={"X-API-Key": "dev-key"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["event_id"] == "evt1"
    assert body["enrichment"]["source"] == "stub"
    with engine.begin() as conn:
        rows = conn.execute(event_table.select()).fetchall()
        assert len(rows) == 1


def test_ingest_event_error(monkeypatch):
    reset_db()
    client = TestClient(app)
    evt = {
        "event_id": "evt2",
        "ts": datetime.utcnow().isoformat(),
        "src": "unit-test",
        "content": {"msg": "hi"},
    }

    def boom(event):  # type: ignore[unused-argument]
        raise RuntimeError("boom")

    monkeypatch.setattr("api.fastapi_app.enrich_event", boom)

    resp = client.post("/ingest/event", json=evt, headers={"X-API-Key": "dev-key"})
    assert resp.status_code == 500
