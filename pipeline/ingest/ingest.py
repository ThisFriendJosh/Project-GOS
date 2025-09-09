from __future__ import annotations
from typing import Any, Dict
from uuid import uuid4
from datetime import datetime


def ingest_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a raw event for processing.

    Ensures the event has an ``event_id`` and timestamp.
    """
    evt = dict(event)
    evt.setdefault("event_id", str(uuid4()))
    evt.setdefault("ts", datetime.utcnow())
    return evt
