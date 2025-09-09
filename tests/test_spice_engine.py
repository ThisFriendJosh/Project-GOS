from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.scoring.spice import Observation, score


def test_spice_engine_deterministic():
    observations = [
        Observation(ttp_family="phishing", observation_type="observed"),
        Observation(ttp_family="ransomware", observation_type="blocked"),
    ]
    result = score(observations)

    # Engine metadata
    assert result["engine_id"] == "spice"
    assert result["engine_version"] == "0.1"

    cfg_path = Path("core/scoring/config/spice.yaml")
    expected_hash = hashlib.sha256(cfg_path.read_bytes()).hexdigest()
    assert result["config_hash"] == expected_hash

    assert result["dimensions"]["impact"] == pytest.approx(1.2)
    assert result["dimensions"]["detection"] == pytest.approx(0.46)
