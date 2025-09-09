from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    from neo4j import Driver, GraphDatabase
except Exception:  # pragma: no cover - fallback when driver not installed
    Driver = GraphDatabase = object  # type: ignore[misc,assignment]

from api.schemas import EventIn


def upsert_event(event: Dict[str, Any]) -> None:
    """Persist an event to Neo4j.

    This is a stub that simulates graph persistence.
    """
    # In a real implementation this would use the Neo4j driver.
    return None


"""Neo4j client utilities for Project GOS.

This module exposes a small wrapper around the official Neo4j Python
driver. It provides helpers for writing events and related domain
objects to the graph while ensuring the constraints defined in
``db/cypher_constraints.cql`` are present. Basic logging and exception
handling are included so callers can understand when writes fail.
"""


logger = logging.getLogger(__name__)


class Neo4jClient:
    """Simple Neo4j wrapper used by the pipeline."""

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str | None = None,
    ) -> None:
        """Initialise the Neo4j driver and ensure constraints exist."""

        try:
            self.driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as exc:  # pragma: no cover - connection errors
            logger.error("Failed to create Neo4j driver: %s", exc)
            raise

        self.database = database
        self._ensure_constraints()

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the underlying driver."""

        self.driver.close()

    def _ensure_constraints(self) -> None:
        """Run the constraint statements bundled with the repo.

        The statements live in ``db/cypher_constraints.cql`` relative to the
        repository root. Each line is executed individually when the client
        is instantiated.
        """

        constraints_path = (
            Path(__file__).resolve().parents[2] / "db" / "cypher_constraints.cql"
        )

        try:
            with (
                open(constraints_path) as handle,
                self.driver.session(database=self.database) as session,
            ):
                for line in handle:
                    query = line.strip()
                    if query:
                        session.run(query)
        except Exception as exc:  # pragma: no cover - primarily startup
            logger.error("Error ensuring constraints: %s", exc)
            raise

    def _run_write(self, query: str, params: Dict[str, Any]) -> None:
        """Execute a write query with basic exception handling."""

        try:
            with self.driver.session(database=self.database) as session:
                session.run(query, **params)
        except Exception as exc:  # pragma: no cover - network/driver issues
            logger.error("Neo4j write failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Domain specific writers
    # ------------------------------------------------------------------
    def write_actor(self, actor_id: str, **props: Any) -> None:
        """Create or update an ``Actor`` node."""

        query = "MERGE (a:Actor {id: $id}) SET a += $props"
        self._run_write(query, {"id": actor_id, "props": props})

    def write_ttp(self, ttp_id: str, **props: Any) -> None:
        """Create or update a ``TTP`` node."""

        query = "MERGE (t:TTP {id: $id}) SET t += $props"
        self._run_write(query, {"id": ttp_id, "props": props})

    def write_event(self, event: EventIn) -> None:
        """Write an ``Event`` and its relationships to the graph."""

        event_query = (
            "MERGE (e:Event {id: $id}) "
            "SET e.ts=$ts, e.src=$src, e.content=$content, e.feats=$feats"
        )
        self._run_write(
            event_query,
            {
                "id": event.event_id,
                "ts": event.ts,
                "src": event.src,
                "content": event.content,
                "feats": event.feats,
            },
        )

        for ttp in getattr(event, "observed_ttp", []) or []:
            rel_query = (
                "MERGE (t:TTP {id: $ttp_id}) "
                "MERGE (e:Event {id: $event_id}) "
                "MERGE (e)-[:OBSERVED]->(t)"
            )
            self._run_write(rel_query, {"ttp_id": ttp, "event_id": event.event_id})

