from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool


def _get_engine(dsn: str | Engine | None) -> Engine:
    if isinstance(dsn, Engine):
        return dsn
    url = dsn or "sqlite://"
    if url.startswith("sqlite"):
        return create_engine(
            url, future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    return create_engine(url, future=True)


def build_spice_report_v22(
    scope: str, scope_id: str, window: Optional[Sequence[str]], dsn: str | Engine | None = None
) -> Dict[str, Any]:
    engine = _get_engine(dsn)
    metadata = MetaData()
    event_table = Table("event", metadata, autoload_with=engine)

    with engine.begin() as conn:
        query = select(event_table.c.event_id, event_table.c.ts, event_table.c.observed_ttp)
        if scope == "event":
            query = query.where(event_table.c.event_id == scope_id)
        elif scope == "incident":
            query = query.where(event_table.c.incident_id == scope_id)
        elif scope == "campaign":
            query = query.where(event_table.c.campaign_id == scope_id)
        if window and len(window) == 2:
            start, end = window
            if start:
                query = query.where(event_table.c.ts >= start)
            if end:
                query = query.where(event_table.c.ts <= end)
        rows = conn.execute(query).fetchall()

    ttp_counts: Dict[str, int] = {}
    for row in rows:
        observed: List[str] = row.observed_ttp or []
        for ttp in observed:
            ttp_counts[ttp] = ttp_counts.get(ttp, 0) + 1

    top_ttps = sorted(ttp_counts.items(), key=lambda kv: kv[1], reverse=True)[:3]
    top_ttp_ids = [ttp for ttp, _ in top_ttps]

    scores = {"event_count": len(rows), "distinct_ttps": len(ttp_counts)}

    blue_coas = [
        {"ttp": ttp, "action": f"Investigate and mitigate {ttp}"}
        for ttp in top_ttp_ids
    ]

    report = {
        "report_id": f"sprt_{scope}_{scope_id}_{int(datetime.utcnow().timestamp())}",
        "version": "2.2",
        "scope": scope,
        "scope_id": scope_id,
        "window": window,
        "scores": scores,
        "top_ttps": top_ttp_ids,
        "paths": {},
        "blue_coas": blue_coas,
        "generated_at": datetime.utcnow().isoformat(),
    }
    return report
