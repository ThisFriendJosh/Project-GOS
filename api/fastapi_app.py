from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .schemas import EventIn, SpiceScope, MapTTPRequest, MapTTPResponse
from .auth import get_api_key
from sim.tickloop import predict_policy_impact  # root-mode import

app = FastAPI(title="Project-GOS API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest/event", dependencies=[Depends(get_api_key)])
def ingest_event(evt: EventIn):
    # TODO: wire to DB
    return {"ok": True, "event_id": evt.event_id}

@app.post("/map/ttp", response_model=MapTTPResponse, dependencies=[Depends(get_api_key)])
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