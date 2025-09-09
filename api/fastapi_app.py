from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, DateTime, JSON, MetaData, String, Table, create_engine
from sqlalchemy.pool import StaticPool

from .schemas import EventIn, MapTTPRequest, MapTTPResponse
from .auth import get_api_key
from sim.tickloop import predict_policy_impact  # root-mode import
from core.mappers.mapper import map_event_to_ttps

from pipeline.graph.neo4j_client import upsert_event as write_graph
from pipeline.normalize.normalize import normalize_event

import os
from datetime import datetime
from uuid import uuid4

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://")
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
else:
    engine = create_engine(DATABASE_URL, future=True)

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

app = FastAPI(title="Project-GOS API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/health")
def health():
    return {"ok": True}


def enrich_event(event: dict) -> tuple[dict, dict]:
    """Normalize event content and mark it as processed."""

    normalized = normalize_event(event)
    meta = {"source": "stub"}
    return normalized, meta


@app.post("/ingest/event", dependencies=[Depends(get_api_key)])
def ingest_event(evt: EventIn):
    try:
        event = evt.model_dump()
        event.setdefault("event_id", str(uuid4()))
        event.setdefault("ts", datetime.utcnow())
        event, meta = enrich_event(event)
        with engine.begin() as conn:
            conn.execute(event_table.insert().values(**event))
        write_graph(event)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "event_id": event["event_id"], "enrichment": meta}


@app.post(
    "/map/ttp", response_model=MapTTPResponse, dependencies=[Depends(get_api_key)]
)
def map_ttp(req: MapTTPRequest):
    observed, probs = map_event_to_ttps(req.event)
    return MapTTPResponse(observed_ttp=observed, probs=probs)

@app.post("/policy/apply", dependencies=[Depends(get_api_key)])
def policy_apply(campaign_id: str, s_amplify: float = 1.0, s_share: float = 1.0):
    return predict_policy_impact(campaign_id, s_amplify, s_share, dsn=None)
