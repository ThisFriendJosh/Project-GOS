"""Deterministic scoring tests for SP!CE and UPDC."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from sqlalchemy import Column, DateTime, JSON, MetaData, String, Table, create_engine
from sqlalchemy.pool import StaticPool

import pytest

# Ensure project root is on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.scoring import build_spice_report_v22, UPDCResult, updc_transform


@pytest.fixture()
def spice_engine():
    """In-memory SQLite engine with the event table schema."""
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata = MetaData()
    Table(
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
    return engine


def test_spice_report_repeatable(spice_engine):
    """SP!CE scoring should be deterministic and within bounds."""
    now = datetime.utcnow()
    events = [
        {
            "event_id": "e1",
            "ts": now,
            "src": "unit-test",
            "content": {},
            "observed_ttp": ["T1000"],
            "campaign_id": "camp1",
        },
        {
            "event_id": "e2",
            "ts": now,
            "src": "unit-test",
            "content": {},
            "observed_ttp": ["T1000", "T2000"],
            "campaign_id": "camp1",
        },
    ]
    with spice_engine.begin() as conn:
        conn.execute(
            Table("event", MetaData(), autoload_with=spice_engine).insert(), events
        )

    report1 = build_spice_report_v22("campaign", "camp1", None, dsn=spice_engine)
    report2 = build_spice_report_v22("campaign", "camp1", None, dsn=spice_engine)

    assert report1["scores"] == report2["scores"]
    assert report1["top_ttps"] == report2["top_ttps"]

    scores = report1["scores"]
    assert scores["event_count"] == len(events)
    assert 0 <= scores["distinct_ttps"] <= scores["event_count"]


def test_updc_repeatable():
    """UPDC transform should be deterministic and produce bounded scores."""
    inputs = (10, 5, 5, 2, 3, 9)
    result1 = updc_transform(*inputs)
    result2 = updc_transform(*inputs)

    assert result1 == result2
    assert isinstance(result1, UPDCResult)

    assert 0 <= result1.RT <= sum(inputs[:3])
    assert 0 <= result1.Q <= inputs[-1]
    assert min(result1.RT, result1.Q) <= result1.CI <= max(result1.RT, result1.Q)
