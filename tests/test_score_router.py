from datetime import datetime
from pathlib import Path
import importlib
import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Column, DateTime, JSON, MetaData, String, Table, create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

os.environ["API_KEY"] = "test"


def build_app(tmp_path: Path):
    # prepare database for spice engine
    db_url = f"sqlite:///{tmp_path / 'spice.db'}"
    engine = create_engine(db_url, future=True)
    metadata = MetaData()
    event_table = Table(
        "event",
        metadata,
        Column("event_id", String, primary_key=True),
        Column("ts", DateTime, nullable=False),
        Column("src", String),
        Column("actor_id", String),
        Column("content", JSON),
        Column("feats", JSON),
        Column("observed_ttp", JSON),
        Column("incident_id", String),
        Column("campaign_id", String),
    )
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            event_table.insert().values(
                event_id="e1",
                ts=datetime.utcnow(),
                src="sensor",
                content={},
                observed_ttp=["t1"],
                incident_id="i1",
                campaign_id="c1",
            )
        )

    cfg = tmp_path / "spice.yml"
    cfg.write_text(f"dsn: {db_url}\n")
    os.environ["SPICE_ENGINE_CONFIG"] = str(cfg)
    root = Path(__file__).resolve().parents[1]
    os.environ["UPDC_ENGINE_CONFIG"] = str(root / "api/routers/config/updc.yml")

    from api.routers import score
    importlib.reload(score)
    app = FastAPI()
    app.include_router(score.router)
    return app


def test_score_updc(monkeypatch):
    app = FastAPI()
    from api.routers import score
    app.include_router(score.router)
    client = TestClient(app)
    resp = client.post(
        "/score/updc",
        json={"I": 1, "S": 1, "M": 1, "W": 1, "n": 1, "R": 1},
        headers={"X-API-Key": "dev-key"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {"RT", "Q", "CI"}


def test_score_spice(tmp_path):
    app = build_app(tmp_path)
    client = TestClient(app)
    resp = client.post(
        "/score/spice",
        json={"scope": "campaign", "scope_id": "c1"},
        headers={"X-API-Key": "dev-key"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scores"]["event_count"] == 1
