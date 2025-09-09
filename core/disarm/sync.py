"""Sync DISARM tactics into the local database.

The script expects the DISARM repository to exist as a git submodule at
``external/disarm``.  The path to the JSON file containing the tactics can be
overridden with the ``DISARM_TACTICS_FILE`` environment variable.  Each tactic
record must provide ``tactic_id``, ``name``, ``description`` and ``phase``
fields.

Running the sync will pull the submodule and upsert the tactics into the
``disarm_tactic`` table.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
from typing import Iterable

from sqlalchemy import Column, MetaData, String, Table, create_engine
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.pool import StaticPool


# Database --------------------------------------------------------------------

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


# Sync routine ----------------------------------------------------------------

def _load_tactics(path: pathlib.Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):  # pragma: no cover - defensive
        raise TypeError("Tactic data must be a list of objects")
    return data


def sync() -> None:
    """Pull the DISARM repository and upsert tactics into the database."""

    disarm_repo = pathlib.Path(os.getenv("DISARM_REPO", "external/disarm"))
    tactics_file = os.getenv("DISARM_TACTICS_FILE")
    if tactics_file:
        tactics_path = pathlib.Path(tactics_file)
    else:
        tactics_path = disarm_repo / "tactics.json"

    # Update the submodule; ignore errors if it is not configured yet.
    subprocess.run(
        [
            "git",
            "submodule",
            "update",
            "--init",
            "--recursive",
            str(disarm_repo),
        ],
        check=False,
    )

    engine = _engine_from_env()
    metadata = MetaData()
    table = _tactic_table(metadata)
    metadata.create_all(engine)

    tactics = _load_tactics(tactics_path)

    with engine.begin() as conn:
        for t in tactics:
            stmt = sqlite_insert(table).values(
                tactic_id=t["tactic_id"],
                name=t["name"],
                description=t.get("description", ""),
                phase=t.get("phase"),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[table.c.tactic_id],
                set_={
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "phase": t.get("phase"),
                },
            )
            conn.execute(stmt)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    sync()
