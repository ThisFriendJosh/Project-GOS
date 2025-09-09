from __future__ import annotations

from datetime import datetime
import pathlib
import sys
import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.schemas import EventIn  # noqa: E402
from core.mappers.mapper import map_event_to_ttps  # noqa: E402
from api.fastapi_app import app  # noqa: E402


def make_event(text: str) -> EventIn:
    return EventIn(
        event_id="evt",
        ts=datetime.utcnow(),
        src="unit-test",
        content={"text": text},
    )


def test_map_event_to_ttps_single_keyword():
    evt = make_event("User reported a phishing email")
    observed, probs = map_event_to_ttps(evt)
    assert observed == ["T1566"]
    assert probs["T1566"] == pytest.approx(1.0)


def test_map_event_to_ttps_multiple_keywords():
    evt = make_event("Detected ransomware and data exfiltration attempt")
    observed, probs = map_event_to_ttps(evt)
    assert set(observed) == {"T1486", "T1041"}
    assert pytest.approx(sum(probs.values())) == 1.0


def test_map_event_to_ttps_no_match():
    evt = make_event("Normal user activity")
    observed, probs = map_event_to_ttps(evt)
    assert observed == []
    assert probs == {}


def test_map_ttp_endpoint():
    client = TestClient(app)
    evt = make_event("phishing attempt").model_dump()
    evt["ts"] = evt["ts"].isoformat()
    resp = client.post("/map/ttp", json={"event": evt}, headers={"X-API-Key": "dev-key"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["observed_ttp"] == ["T1566"]
    assert body["probs"]["T1566"] == pytest.approx(1.0)

