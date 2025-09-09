"""Deterministic SPICE scoring engine.

This module provides a very small, deterministic scoring engine that
assigns observations to high level dimensions.  The implementation is
purposefully tiny – it merely demonstrates how a YAML based
configuration can drive a repeatable scoring process.  The behaviour is
fully deterministic; the same set of observations will always yield the
same scores.

The engine exposes a single :func:`score` function.  It accepts an
iterable of observations where each observation contains a ``ttp_family``
identifier and an ``observation_type``.  A configuration file supplies
dimension weights and observation modifiers.  A static mapping matrix in
this module determines which dimensions are affected by a given
``(ttp_family, observation_type)`` combination.

The returned dictionary includes metadata about the engine such as an
identifier, version and the hash of the configuration that was used to
produce the scores.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Dict, Any
import hashlib
import json

ENGINE_ID = "spice"
ENGINE_VERSION = "0.1"

CONFIG_PATH = Path(__file__).with_name("config").joinpath("spice.yaml")


@dataclass
class Observation:
    """Minimal representation of an observation."""

    ttp_family: str
    observation_type: str


# ---------------------------------------------------------------------------
# Configuration helpers


def _load_config(path: Path | None = None) -> Dict[str, Any]:
    path = Path(path or CONFIG_PATH)
    data = path.read_text()
    cfg = json.loads(data)
    cfg["hash"] = hashlib.sha256(data.encode()).hexdigest()
    return cfg


# ---------------------------------------------------------------------------
# Mapping matrix

# Dimension -> TTP family -> observation type -> base value
MAPPING_MATRIX: Dict[str, Dict[str, Dict[str, float]]] = {
    "impact": {
        "phishing": {"observed": 1.0, "blocked": 0.5},
        "ransomware": {"observed": 5.0, "blocked": 2.0},
    },
    "detection": {
        "phishing": {"observed": 0.5, "blocked": 1.0},
        "ransomware": {"observed": 1.0, "blocked": 1.3},
    },
}


# ---------------------------------------------------------------------------
# Public API


def score(observations: Iterable[Observation], config_path: Path | None = None) -> Dict[str, Any]:
    """Score ``observations`` and return dimension values.

    Parameters
    ----------
    observations:
        Iterable of :class:`Observation` instances.
    config_path:
        Optional path to a YAML configuration file.  When omitted the
        default configuration shipped with the package is used.
    """

    cfg = _load_config(config_path)
    dim_scores: Dict[str, float] = {d: 0.0 for d in cfg["dimensions"]}
    modifiers = cfg.get("modifiers", {})

    for obs in observations:
        mod = modifiers.get(obs.observation_type, 1.0)
        for dim, families in MAPPING_MATRIX.items():
            value = families.get(obs.ttp_family, {}).get(obs.observation_type)
            if value is not None:
                dim_scores[dim] += value * mod

    # Apply dimension weights
    for dim, props in cfg["dimensions"].items():
        weight = props.get("weight", 1.0)
        dim_scores[dim] *= weight

    return {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "config_hash": cfg["hash"],
        "dimensions": dim_scores,
    }


__all__ = ["Observation", "score"]

