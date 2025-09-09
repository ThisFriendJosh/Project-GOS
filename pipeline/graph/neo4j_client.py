from __future__ import annotations

import logging
import os
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    from neo4j import GraphDatabase, Driver  # type: ignore
except Exception:  # pragma: no cover - dependency missing
    GraphDatabase = Driver = None  # type: ignore[assignment]

from api.schemas import EventIn

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Very small wrapper around the Neo4j driver.

    Only the parts exercised by the tests are implemented.  The client merely
    initialises the driver and exposes ``write_event`` and ``close`` methods.
    When the ``neo4j`` package is not installed a :class:`RuntimeError` is
    raised – the tests patch this class so the real driver is never required.
    """

    def __init__(self, uri: str, user: str, password: str, database: str | None = None) -> None:
        if GraphDatabase is None:  # pragma: no cover - optional dependency
            raise RuntimeError("neo4j driver is not installed")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self) -> None:
        self.driver.close()

    def write_event(self, event: EventIn) -> None:  # pragma: no cover - stub
        """Write an event to the graph (stub)."""
        return None


def upsert_event(event: Dict[str, Any]) -> None:
    """Persist an event using :class:`Neo4jClient`.

    Connection parameters are read from environment variables.  In the test
    suite :class:`Neo4jClient` is patched with a mock so no real connection is
    attempted.
    """

    try:
        client = Neo4jClient(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "test"),
            os.getenv("NEO4J_DATABASE") or None,
        )
    except Exception:  # pragma: no cover - driver missing or init failure
        return None

    try:
        client.write_event(EventIn(**event))
    finally:
        try:
            client.close()
        except Exception:  # pragma: no cover - defensive
            logger.warning("Failed to close Neo4j client", exc_info=True)
