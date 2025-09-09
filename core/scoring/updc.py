"""UPDC scoring engine using configurable coefficients.

The engine performs a deterministic transformation of the six input values
``I``, ``S``, ``M``, ``W``, ``n`` and ``R`` into three derived metrics
``RT``, ``Q`` and ``CI``.  Coefficients and guard values are loaded from the
``updc.yaml`` configuration file in this package.

In addition to the computed metrics the returned :class:`UpdcScore` also
contains ``engine_id``, ``engine_version`` and ``config_hash`` for traceability
purposes.  ``metadata`` captures the original inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from pathlib import Path
from typing import Any, Dict

import hashlib
import json

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "updc.yaml"


@dataclass(frozen=True)
class UpdcScore:
    """Result of running :class:`UpdcEngine`."""

    engine_id: str
    engine_version: str
    config_hash: str
    RT: float
    Q: float
    CI: float
    metadata: Dict[str, Any]


class UpdcEngine:
    """Scoring engine for the UPDC transformation."""

    engine_id = "updc"
    engine_version = "1.0"

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or CONFIG_PATH
        config_bytes = self.config_path.read_bytes()
        self.config_hash = hashlib.sha256(config_bytes).hexdigest()
        self.config = json.loads(config_bytes)

    # ------------------------------------------------------------------
    def score(self, I: Real, S: Real, M: Real, W: Real, n: int, R: Real) -> UpdcScore:
        """Return the deterministic UPDC score for the supplied inputs."""

        numeric_inputs: Dict[str, Real] = {"I": I, "S": S, "M": M, "W": W, "R": R}
        for name, value in numeric_inputs.items():
            if not isinstance(value, Real):
                raise TypeError(f"{name} must be a real number")

        if not isinstance(n, int):
            raise TypeError("n must be an integer")

        guards = self.config.get("guards", {})
        if n < guards.get("min_n", 1):
            raise ValueError("n must be a positive integer")

        coeff = self.config["coefficients"]
        denom = coeff["rt"]["W"] * W + coeff["rt"]["n"] * n
        if denom == 0:
            raise ValueError("W + n cannot be zero when computing RT")

        rt_num = (
            coeff["rt"]["I"] * I
            + coeff["rt"]["S"] * S
            + coeff["rt"]["M"] * M
        )
        rt = rt_num / denom
        q = coeff["q"]["R"] * R / (coeff["q"]["n"] * n)
        ci = coeff["ci"]["RT"] * rt + coeff["ci"]["Q"] * q

        metadata = {
            "inputs": {
                "I": float(I),
                "S": float(S),
                "M": float(M),
                "W": float(W),
                "n": int(n),
                "R": float(R),
            }
        }

        return UpdcScore(
            engine_id=self.engine_id,
            engine_version=self.engine_version,
            config_hash=self.config_hash,
            RT=float(rt),
            Q=float(q),
            CI=float(ci),
            metadata=metadata,
        )


__all__ = ["UpdcEngine", "UpdcScore"]
