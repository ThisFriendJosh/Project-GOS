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
    scope: Literal["event", "incident", "campaign"]
    scope_id: str
    version: Literal["1.0", "2.2"] = "2.2"
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


class UpdcIn(BaseModel):
    I: float
    S: float
    M: float
    W: float
    n: int
    R: float


class UpdcOut(BaseModel):
    RT: float
    Q: float
    CI: float
