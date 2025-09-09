"""DISARM tactic registry backed by the local database."""

from __future__ import annotations

import os

from sqlalchemy import Column, MetaData, String, Table, create_engine, func, select
from sqlalchemy.pool import StaticPool


def _engine_from_env():
    url = os.getenv("DATABASE_URL", "sqlite://")
    if url.startswith("sqlite"):
        return create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, future=True)


def _tactic_table(metadata: MetaData) -> Table:
    return Table(
        "disarm_tactic",
        metadata,
        Column("tactic_id", String, primary_key=True),
        Column("name", String, nullable=False),
        Column("description", String, nullable=False),
        Column("phase", String, nullable=True),
    )


class DisarmRegistry:
    """Simple wrapper around the ``disarm_tactic`` table."""

    def __init__(self) -> None:
        self.engine = _engine_from_env()
        self.metadata = MetaData()
        self.table = _tactic_table(self.metadata)
        self.metadata.create_all(self.engine)

    def search(self, q: str = "", phase: str | None = None) -> list[dict]:
        stmt = select(self.table)
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(
                func.lower(self.table.c.name).like(like)
                | func.lower(self.table.c.description).like(like)
            )
        if phase:
            stmt = stmt.where(self.table.c.phase == phase)
        with self.engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [dict(r) for r in rows]
