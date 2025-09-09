"""Domain models used by scoring engines."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Evidence(BaseModel):
    """A single piece of supporting information for an observation."""

    kind: Optional[str] = None
    value: Optional[str] = None
    notes: Optional[str] = None


class TTPRef(BaseModel):
    """Reference to a MITRE ATT&CK technique or similar TTP."""

    ttp_id: str
    name: Optional[str] = None


class Actor(BaseModel):
    """An actor participating in a scenario."""

    name: str
    role: Optional[str] = None


class Observation(BaseModel):
    """An observed actor performing a TTP with associated evidence."""

    actor: Optional[Actor] = None
    ttp: Optional[TTPRef] = None
    evidence: List[Evidence] = []


class Scenario(BaseModel):
    """A collection of observations describing a scenario."""

    name: Optional[str] = None
    description: Optional[str] = None
    observations: List[Observation] = []
