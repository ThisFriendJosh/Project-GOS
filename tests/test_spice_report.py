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


def test_spice_report_scoring():
    reset_db()
    now = datetime.utcnow()
    events = [
        {
            "event_id": "e1",
            "ts": now,
            "src": "unit-test",
            "content": {},
            "observed_ttp": ["T1000"],
            "campaign_id": "camp1",
        },
        {
            "event_id": "e2",
            "ts": now,
            "src": "unit-test",
            "content": {},
            "observed_ttp": ["T1000", "T2000"],
            "campaign_id": "camp1",
        },
    ]
    with engine.begin() as conn:
        conn.execute(event_table.insert(), events)

    client = TestClient(app)
    resp = client.post(
        "/spice/report",
        json={"scope": "campaign", "scope_id": "camp1"},
        headers={"X-API-Key": "dev-key"},
    )
    assert resp.status_code == 200
    body = resp.json()
    for key in [
        "report_id",
        "version",
        "scope",
        "scope_id",
        "scores",
        "top_ttps",
        "paths",
        "blue_coas",
        "generated_at",
    ]:
        assert key in body
    assert body["scores"]["event_count"] == 2
    assert body["scores"]["distinct_ttps"] == 2
    assert body["top_ttps"] == ["T1000", "T2000"]
    assert len(body["blue_coas"]) == 2
    assert body["blue_coas"][0]["ttp"] == "T1000"
