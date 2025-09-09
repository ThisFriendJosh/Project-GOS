from __future__ import annotations
import os
from typing import Any, Dict


def upsert_event(event: Dict[str, Any]) -> None:
    """Persist an event to Neo4j.

    Instantiate :class:`Neo4jClient` using connection parameters from
    environment variables and write the provided ``event`` to the graph.
    ``event`` is expected to be a mapping compatible with
    :class:`api.schemas.EventIn`.
    """

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "test")
    database = os.getenv("NEO4J_DATABASE") or None

    try:
        client = Neo4jClient(uri, user, password, database)
    except Exception:  # pragma: no cover - optional dependency or connection
        logger.warning("Neo4j client unavailable", exc_info=True)
        return

    try:
        client.write_event(EventIn(**event))
    except Exception:  # pragma: no cover - write issues
        logger.warning("Neo4j write failed", exc_info=True)
    finally:
        try:
            client.close()
        except Exception:  # pragma: no cover - close errors
            logger.warning("Failed to close Neo4j client", exc_info=True)
"""Neo4j client utilities for Project GOS.

This module exposes a small wrapper around the official Neo4j Python
driver.  It provides helpers for writing events and related domain
objects to the graph while ensuring the constraints defined in
``db/cypher_constraints.cql`` are present.  Basic logging and exception
handling are included so callers can understand when writes fail.
"""
import logging
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    from neo4j import Driver, GraphDatabase
except Exception:  # pragma: no cover - import fallback
    Driver = Any  # type: ignore

    class GraphDatabase:  # type: ignore
        @staticmethod
        def driver(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401 - dynamic
            raise RuntimeError("neo4j driver is not installed")

from api.schemas import EventIn


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
        repository root.  Each line is executed individually when the client
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
        params = {
            "id": event.event_id,
            "ts": event.ts.isoformat(),
            "src": event.src,
            "content": event.content,
            "feats": event.feats,
        }
        self._run_write(event_query, params)

        if event.actor_id:
            self.write_actor(event.actor_id)
            rel = (
                "MATCH (e:Event {id:$eid}), (a:Actor {id:$aid}) "
                "MERGE (a)-[:ACTOR_OF]->(e)"
            )
            self._run_write(rel, {"eid": event.event_id, "aid": event.actor_id})

        for ttp_id in event.observed_ttp:
            self.write_ttp(ttp_id)
            rel = (
                "MATCH (e:Event {id:$eid}), (t:TTP {id:$tid}) "
                "MERGE (e)-[:OBSERVED]->(t)"
            )
            self._run_write(rel, {"eid": event.event_id, "tid": ttp_id})

        if event.incident_id:
            incident_query = "MERGE (i:Incident {id:$id})"
            self._run_write(incident_query, {"id": event.incident_id})
            rel = (
                "MATCH (e:Event {id:$eid}), (i:Incident {id:$iid}) "
                "MERGE (e)-[:PART_OF]->(i)"
            )
            self._run_write(rel, {"eid": event.event_id, "iid": event.incident_id})

        if event.campaign_id:
            campaign_query = "MERGE (c:Campaign {id:$id})"
            self._run_write(campaign_query, {"id": event.campaign_id})
            rel = (
                "MATCH (e:Event {id:$eid}), (c:Campaign {id:$cid}) "
                "MERGE (e)-[:PART_OF]->(c)"
            )
            self._run_write(rel, {"eid": event.event_id, "cid": event.campaign_id})
