from __future__ import annotations
from typing import Any, Dict, Tuple


def enrich_event(event: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Enrich an event with additional context.

    Returns the enriched event and any metadata generated during enrichment.
    """
    metadata: Dict[str, Any] = {"source": "stub"}
    # Example enrichment flag
    feats = event.get("feats", {})
    feats["enriched"] = True
    event["feats"] = feats
    return event, metadata
