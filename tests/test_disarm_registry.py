import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.disarm.registry import DisarmRegistry
from core.disarm.sync import sync


def _write_sample(tmp_path: Path) -> None:
    disarm_dir = tmp_path / "external" / "disarm"
    disarm_dir.mkdir(parents=True)
    tactics = [
        {
            "tactic_id": "TA01",
            "name": "Tactic One",
            "description": "Alpha tactic",
            "phase": "Plan",
        },
        {
            "tactic_id": "TA02",
            "name": "Tactic Two",
            "description": "Bravo tactic",
            "phase": "Act",
        },
    ]
    (disarm_dir / "tactics.json").write_text(json.dumps(tactics))
    os.environ["DISARM_TACTICS_FILE"] = str(disarm_dir / "tactics.json")


def test_search_filters(tmp_path):
    db_path = tmp_path / "t.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    _write_sample(tmp_path)
    sync()

    reg = DisarmRegistry()
    all_rows = reg.search(q="tactic")
    assert {r["tactic_id"] for r in all_rows} == {"TA01", "TA02"}

    plan_rows = reg.search(q="tactic", phase="Plan")
    assert len(plan_rows) == 1
    assert plan_rows[0]["tactic_id"] == "TA01"
