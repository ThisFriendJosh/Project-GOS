"""Scoring engine utilities."""

from .registry import cfg_hash, get, register

__all__ = ["register", "get", "cfg_hash"]
"""Scoring modules exposed at :mod:`core.scoring`."""

from . import updc

__all__ = ["updc"]
