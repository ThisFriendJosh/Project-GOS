"""UPDC Engine.

This module implements a simple mathematical transformation used by the test
suite.  The transformation accepts six numeric inputs ``I``, ``S``, ``M``,
``W``, ``n`` and ``R`` and returns three derived values ``RT``, ``Q`` and
``CI``.

The intent of the implementation is to provide a well documented example of a
small processing engine with proper validation of the inputs.  The exact
mathematics are intentionally straightforward:

``RT``
    Response time calculated as ``(I + S + M) / (W + n)``.  ``W + n`` must be
    non-zero, otherwise a :class:`ValueError` is raised.

``Q``
    Quality metric derived from ``R / n``.  ``n`` must be a positive integer.

``CI``
    Composite index defined as ``0.5 * (RT + Q)`` – the mean of ``RT`` and
    ``Q``.

The :func:`updc_transform` function is the public entry point and returns a
dataclass :class:`UPDCResult`.
"""

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


def updc_transform(I: Real, S: Real, M: Real, W: Real, n: int, R: Real) -> UPDCResult:
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

