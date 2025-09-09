from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.schemas import EventIn
from pipeline.graph.neo4j_client import upsert_event


def test_upsert_event_calls_client(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://example.com")
    monkeypatch.setenv("NEO4J_USER", "user")
    monkeypatch.setenv("NEO4J_PASSWORD", "pass")
    monkeypatch.setenv("NEO4J_DATABASE", "db")

    event = {
        "event_id": "evt1",
        "ts": datetime.utcnow(),
        "src": "unit-test",
        "content": {"text": "hello"},
    }

    mock_client = MagicMock()
    with patch("pipeline.graph.neo4j_client.Neo4jClient", return_value=mock_client) as mock_cls:
        upsert_event(event)

    mock_cls.assert_called_once_with("bolt://example.com", "user", "pass", "db")
    mock_client.write_event.assert_called_once()
    arg = mock_client.write_event.call_args[0][0]
    assert isinstance(arg, EventIn)
    assert arg.event_id == "evt1"
    mock_client.close.assert_called_once()
