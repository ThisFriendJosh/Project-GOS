"""Base types for scoring engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.schemas import Scenario


@dataclass
class ScoreResult:
    """Outcome of a scoring engine."""

    score: float
    details: dict | None = None


class Engine(Protocol):
    """Protocol for scoring engines."""

    def score(self, scenario: Scenario) -> ScoreResult: ...
