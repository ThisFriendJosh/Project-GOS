from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, DateTime, JSON, MetaData, String, Table, create_engine
from sqlalchemy.pool import StaticPool

from .schemas import EventIn, SpiceScope, MapTTPRequest, MapTTPResponse
from .auth import get_api_key
from sim.tickloop import predict_policy_impact  # root-mode import

from pipeline.ingest.ingest import ingest_event as ingest_stage
from pipeline.normalize.normalize import normalize_event
from pipeline.enrich.enrich import enrich_event
from pipeline.graph.neo4j_client import upsert_event as write_graph

import os

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


@app.post("/ingest/event", dependencies=[Depends(get_api_key)])
def ingest_event(evt: EventIn):
    try:
        event = ingest_stage(evt.model_dump())
        event = normalize_event(event)
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
    # TODO: replace with real mapper
    return MapTTPResponse(observed_ttp=[], probs={})


@app.post("/spice/report", dependencies=[Depends(get_api_key)])
def spice_report(sc: SpiceScope):
    # TODO: call SP!CE v2.2 builder
    return {"ok": True, "scope": sc.scope, "scope_id": sc.scope_id}


@app.post("/policy/apply", dependencies=[Depends(get_api_key)])
def policy_apply(campaign_id: str, s_amplify: float = 1.0, s_share: float = 1.0):
    return predict_policy_impact(campaign_id, s_amplify, s_share, dsn=None)
