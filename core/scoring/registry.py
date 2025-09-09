"""Registry for scoring engines keyed by configuration."""

from __future__ import annotations

import hashlib
import json
from typing import Dict

from .base import Engine

_REGISTRY: Dict[str, Engine] = {}


def cfg_hash(cfg: dict) -> str:
    """Return a stable hash for a configuration dictionary."""

    data = json.dumps(cfg, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def register(cfg: dict, engine: Engine) -> str:
    """Register an engine for a configuration and return its hash."""

    h = cfg_hash(cfg)
    _REGISTRY[h] = engine
    return h


def get(cfg: dict) -> Engine:
    """Retrieve an engine for *cfg* raising ``KeyError`` if missing."""

    h = cfg_hash(cfg)
    return _REGISTRY[h]
