"""Tests for the UPDC scoring engine."""

from pathlib import Path
import sys

import pytest

# Ensure the project root is on the import path so ``core`` can be imported
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.scoring.updc import UpdcEngine, UpdcScore


def test_updc_score_basic() -> None:
    """Verify typical scoring output."""

    engine = UpdcEngine()
    result = engine.score(10, 5, 5, 2, 3, 9)
    assert isinstance(result, UpdcScore)
    assert result.RT == pytest.approx(4.0)
    assert result.Q == pytest.approx(3.0)
    assert result.CI == pytest.approx(3.5)
    assert result.engine_id == "updc"
    assert result.engine_version == "1.0"
    assert result.config_hash
    assert "inputs" in result.metadata


def test_updc_score_invalid_n() -> None:
    """``n`` must be positive."""

    engine = UpdcEngine()
    with pytest.raises(ValueError):
        engine.score(1, 1, 1, 1, 0, 1)


def test_updc_score_zero_denom() -> None:
    """The denominator ``W + n`` cannot be zero."""

    engine = UpdcEngine()
    with pytest.raises(ValueError):
        engine.score(1, 1, 1, -3, 3, 1)


def test_updc_score_type_error() -> None:
    """Non-numeric inputs raise :class:`TypeError`."""

    engine = UpdcEngine()
    with pytest.raises(TypeError):
        engine.score("a", 1, 1, 1, 1, 1)
