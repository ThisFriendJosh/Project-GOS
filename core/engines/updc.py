"""Placeholder engine module for UPDC.

This stub ensures the module can be imported via ``core.engines``.
"""

# I,S,M,W,n,R → RT,Q,CI

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Dict


@dataclass(frozen=True)
class UPDCResult:
    """Container for the results of :func:`updc_transform`.

    Attributes
    ----------
    RT:
        Response time value.
    Q:
        Quality metric.
    CI:
        Composite index derived from ``RT`` and ``Q``.
    """

    RT: float
    Q: float
    CI: float


def updc_transform(
    I: Real, S: Real, M: Real, W: Real, n: int, R: Real
) -> UPDCResult:  # noqa: E741
    """Transform six input parameters into three derived values.

    Parameters
    ----------
    I, S, M, W, R:
        Real numbers representing the input parameters.
    n:
        Positive integer used as a divisor in the transformation.  Must be
        greater than zero.

    Returns
    -------
    UPDCResult
        Dataclass containing ``RT``, ``Q`` and ``CI``.

    Raises
    ------
    TypeError
        If any supplied argument is not a real number (except ``n`` which must
        be an integer).
    ValueError
        If ``n`` is not positive or if ``W + n`` equals zero.
    """

    # Validate numeric inputs (excluding ``n`` which is handled separately).
    numeric_inputs: Dict[str, Real] = {"I": I, "S": S, "M": M, "W": W, "R": R}
    for name, value in numeric_inputs.items():
        if not isinstance(value, Real):
            raise TypeError(f"{name} must be a real number")

    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n <= 0:
        raise ValueError("n must be a positive integer")

    denom_rt = W + n
    if denom_rt == 0:
        raise ValueError("W + n cannot be zero when computing RT")

    # Calculate the derived metrics.
    rt = (I + S + M) / denom_rt
    q = R / n
    ci = 0.5 * (rt + q)

    return UPDCResult(RT=float(rt), Q=float(q), CI=float(ci))


__all__ = ["UPDCResult", "updc_transform"]
