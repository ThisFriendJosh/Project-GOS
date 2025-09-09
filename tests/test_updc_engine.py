"""Tests for the UPDC engine transformation."""

from pathlib import Path
import sys

import pytest

# Ensure the project root is on the import path so ``core`` can be imported
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.engines.updc import UPDCResult, updc_transform


def test_updc_transform_basic():
    """Verify typical transformation output."""

    result = updc_transform(10, 5, 5, 2, 3, 9)
    assert isinstance(result, UPDCResult)
    assert result.RT == pytest.approx(4.0)
    assert result.Q == pytest.approx(3.0)
    assert result.CI == pytest.approx(3.5)


def test_updc_transform_invalid_n():
    """``n`` must be positive."""

    with pytest.raises(ValueError):
        updc_transform(1, 1, 1, 1, 0, 1)


def test_updc_transform_zero_denom():
    """The denominator ``W + n`` cannot be zero."""

    with pytest.raises(ValueError):
        updc_transform(1, 1, 1, -3, 3, 1)


def test_updc_transform_type_error():
    """Non-numeric inputs raise :class:`TypeError`."""

    with pytest.raises(TypeError):
        updc_transform("a", 1, 1, 1, 1, 1)

