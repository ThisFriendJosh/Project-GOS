#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Merge Project-GOS structure into existing subfolder safely.
# - Creates only missing dirs/files (no overwrite).
# - With --force, backs up existing files as *.bak.<timestamp>
#   before writing the new version.
# - Creates a git branch, commits, and opens a PR if gh exists.
# ============================================================

SUBDIR="Project-GOS"
BRANCH="feat/project-gos-structure"
API_KEY_PLACEHOLDER="dev-key"
FORCE=0
TS="$(date +%Y%m%d_%H%M%S)"

if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
  echo ">> FORCE mode enabled: existing files will be backed up then replaced."
fi

# --- sanity checks ---
if [[ ! -d .git ]]; then
  echo "!! This doesn't look like a git repo. Run from your repo root."
  exit 1
fi

if [[ ! -d "${SUBDIR}" ]]; then
  echo "!! Expected subfolder '${SUBDIR}' to exist. Create it first or update SUBDIR in this script."
  exit 1
fi
# --- git branch ---
if ! git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  echo ">> Creating branch $BRANCH"
  git checkout -b "$BRANCH"
else
  echo ">> Using existing branch $BRANCH"
  git checkout "$BRANCH"
fi

ROOT="${SUBDIR}"

# --- helper: write file safely ---
write_file() {
  local path="$1"
  local content="$2"

  if [[ -f "$path" ]]; then
    if [[ $FORCE -eq 1 ]]; then
      # Compare content; if different, back up then replace
      if ! diff -q <(printf "%s" "$content") "$path" >/dev/null 2>&1; then
        cp "$path" "$path.bak.$TS"
        printf "%s" "$content" > "$path"
        echo "  ~ Updated (backup saved): $path"
      else
        echo "  = Unchanged: $path"
      fi
    else
      echo "  = Exists (kept): $path"
    fi
  else
    printf "%s" "$content" > "$path"
    echo "  + Created: $path"
  fi
}

# --- create directories ---
echo ">> Ensuring directory structure under ${ROOT}/"
mkdir -p "${ROOT}"/core/{spice,disarm,mappers,metrics,engines}
mkdir -p "${ROOT}"/pipeline/{ingest,normalize,enrich,graph}
mkdir -p "${ROOT}"/sim "${ROOT}"/api "${ROOT}"/db "${ROOT}"/ui/webapp "${ROOT}"/ops

# --- .gitkeep placeholders for empty dirs ---
for d in \
  core/spice core/disarm core/mappers core/metrics core/engines \
  pipeline/ingest pipeline/normalize pipeline/enrich pipeline/graph \
  ui/webapp
do
  f="${ROOT}/${d}/.gitkeep"
  [[ -f "$f" ]] || { echo "" > "$f"; echo "  + Created: $f"; }
done

# --- minimal working stubs (ONLY created if missing, unless --force) ---

# sim/tickloop.py
write_file "${ROOT}/sim/tickloop.py" "$(cat <<'PY'
# Minimal simulation stub; replace with real loop.
def predict_policy_impact(campaign_id, s_amp=None, s_share=None, dsn=None):
    base = 1000
    amp = s_amp if s_amp is not None else 1.0
    shr = s_share if s_share is not None else 1.0
    return {
        "baseline_reach": base,
        "projected_reach": int(base*amp*(1+0.5*shr)),
        "eta": {"amplify": amp, "share": shr}
    }
PY
)"

# api/schemas.py
write_file "${ROOT}/api/schemas.py" "$(cat <<'PY'
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

class EventIn(BaseModel):
    event_id: str
    ts: datetime
    src: str
    actor_id: Optional[str] = None
    content: Dict[str, Any]
    feats: Dict[str, Any] = {}
    observed_ttp: List[str] = []
    incident_id: Optional[str] = None
    campaign_id: Optional[str] = None

class TTP(BaseModel):
    ttp_id: str
    name: str
    phase: Optional[str] = None
    description: Optional[str] = None
    tactics: List[str] = []
    techniques: List[str] = []
    detection: Optional[str] = None
    mitigation: Optional[str] = None
    refs: Dict[str, Any] = {}
    xref: Dict[str, Any] = {}

class SpiceScope(BaseModel):
    scope: Literal["event","incident","campaign"]
    scope_id: str
    version: Literal["1.0","2.2"] = "2.2"
    window: Optional[List[str]] = None

class MapTTPRequest(BaseModel):
    event: EventIn

class MapTTPResponse(BaseModel):
    observed_ttp: List[str]
    probs: Dict[str, float]

class PolicyApplyRequest(BaseModel):
    s_amplify: float | None = None
    s_share: float | None = None
    campaign_id: Optional[str] = None
PY
)"

# api/auth.py
write_file "${ROOT}/api/auth.py" "$(cat <<PY
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(key: str | None = Depends(api_key_header)):
    if key != "${API_KEY_PLACEHOLDER}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return key
PY
)"

# api/fastapi_app.py
write_file "${ROOT}/api/fastapi_app.py" "$(cat <<'PY'
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .schemas import EventIn, SpiceScope, MapTTPRequest, MapTTPResponse
from .auth import get_api_key
from ..sim.tickloop import predict_policy_impact

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
PY
)"

# core/disarm/registry.py
write_file "${ROOT}/core/disarm/registry.py" "$(cat <<'PY'
# Placeholder registry; replace with DB-backed search.
class DisarmRegistry:
    def search(self, q: str = "", phase: str | None = None):
        return []
PY
)"

# core/disarm/sync.py
write_file "${ROOT}/core/disarm/sync.py" "$(cat <<'PY'
# TODO: add DISARM submodule sync + DB upsert here
if __name__ == "__main__":
    print("Run: git submodule add <DISARM_GIT_URL> external/disarm")
PY
)"

# core/mappers/mapper.py
write_file "${ROOT}/core/mappers/mapper.py" "$(cat <<'PY'
from typing import Dict, List, Tuple
from ...api.schemas import EventIn

def map_event_to_ttps(evt: EventIn) -> Tuple[List[str], Dict[str,float]]:
    # TODO: implement heuristics/ML mapping
    return [], {}
PY
)"

# core/spice/v22.py
write_file "${ROOT}/core/spice/v22.py" "$(cat <<'PY'
from datetime import datetime

def build_spice_report_v22(scope: str, scope_id: str, window, dsn: str=None):
    # TODO: implement full SP!CE v2.2 scoring
    return {
        "report_id": f"sprt_{scope}_{scope_id}_{int(datetime.utcnow().timestamp())}",
        "version":"2.2","scope":scope,"scope_id":scope_id,
        "scores":{},"top_ttps":[],"paths":{},"blue_coas":[],
        "generated_at": datetime.utcnow().isoformat()
    }
PY
)"

# db/ddl.sql
write_file "${ROOT}/db/ddl.sql" "$(cat <<'SQL'
CREATE TABLE IF NOT EXISTS ttp(
  ttp_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  phase TEXT,
  description TEXT,
  tactics TEXT[],
  techniques TEXT[],
  detection TEXT,
  mitigation TEXT,
  refs JSONB,
  xref JSONB
);
CREATE TABLE IF NOT EXISTS event(
  event_id TEXT PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  src TEXT,
  actor_id TEXT,
  content JSONB,
  feats JSONB,
  observed_ttp TEXT[],
  incident_id TEXT,
  campaign_id TEXT
);
CREATE TABLE IF NOT EXISTS incident(
  incident_id TEXT PRIMARY KEY,
  window TSRANGE NOT NULL,
  seed_event_ids TEXT[],
  dominant_ttps TEXT[],
  stats JSONB
);
CREATE TABLE IF NOT EXISTS spice_report(
  report_id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  scope TEXT NOT NULL,
  scope_id TEXT NOT NULL,
  window TSRANGE,
  scores JSONB,
  top_ttps TEXT[],
  paths JSONB,
  blue_coas JSONB,
  generated_at TIMESTAMPTZ DEFAULT now()
);
SQL
)"

# db/cypher_constraints.cql
write_file "${ROOT}/db/cypher_constraints.cql" "$(cat <<'CQL'
CREATE CONSTRAINT actor_id IF NOT EXISTS FOR (a:Actor) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT ttp_id   IF NOT EXISTS FOR (t:TTP)   REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT campaign_id IF NOT EXISTS FOR (c:Campaign) REQUIRE c.id IS UNIQUE;
CQL
)"

# ops/docker-compose.yml
write_file "${ROOT}/ops/docker-compose.yml" "$(cat <<'YAML'
version: "3.9"
services:
  api:
    image: python:3.11-slim
    working_dir: /app
    command: bash -lc "pip install -r requirements.txt && uvicorn Project-GOS.api.fastapi_app:app --host 0.0.0.0 --port 8000"
    volumes:
      - ./:/app
    ports:
      - "8000:8000"
YAML
)"

# Makefile
write_file "${ROOT}/Makefile" "$(cat <<'MK'
.PHONY: up
up:
\tdocker compose -f ops/docker-compose.yml up --build
MK
)"

# requirements.txt (placed at repo root if absent; else in subdir)
REQ_TARGET="requirements.txt"
if [[ -f "${REQ_TARGET}" && ${FORCE} -eq 0 ]]; then
  echo "  = Exists (kept): ${REQ_TARGET}"
else
  write_file "${REQ_TARGET}" "$(cat <<'REQ'
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
REQ
)"
fi

# README drop for PR context
write_file "${ROOT}/README_PROJECT_GOS.md" "$(cat <<'MD'
# Project-GOS Structure Drop
This change introduces the modular tree for OSINT → PSYOP sim with SP!CE/DISARM support.
Only missing files were created; existing files were left untouched (unless --force used).
Replace stubs with full implementations as you integrate.
MD
)"

# --- git add/commit ---
echo ">> Staging changes"
git add "${ROOT}" || true
git add requirements.txt || true

if ! git diff --cached --quiet; then
  git commit -m "feat(Project-GOS): scaffold core/pipeline/sim/api/db/ui/ops structure (safe merge)"
else
  echo ">> Nothing to commit (tree already present)."
fi

# --- optional PR ---
if command -v gh >/dev/null 2>&1; then
  echo ">> Opening PR via gh (if one doesn’t already exist)"
  gh pr create --fill --base main --title "Project-GOS: structure & API stubs" --body-file "${ROOT}/README_PROJECT_GOS.md" || true
else
  echo ">> gh not found; push & open PR manually:"
  echo "   git push -u origin ${BRANCH}"
fi

echo ">> Done. Review the branch '${BRANCH}' and open a PR if needed."
