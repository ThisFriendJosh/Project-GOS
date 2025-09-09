from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

try:  # YAML is optional; fall back to JSON if unavailable
    import yaml
except Exception:  # pragma: no cover - fall back if PyYAML missing
    yaml = None

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_api_key
from ..schemas import SpiceScope, UpdcIn, UpdcOut

# ---------------------------------------------------------------------------
# Dynamic engine loading

ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, relative: Path):
    """Load a module without importing the ``core`` package."""
    import importlib.util

    module_path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_spice_mod = _load_module("spice_v22", Path("core/spice/v22.py"))
_build_spice_report_v22 = _spice_mod.build_spice_report_v22

try:  # ``core/engines/updc.py`` may not parse in minimal environments
    _updc_mod = _load_module("updc_engine", Path("core/engines/updc.py"))
    _updc_transform = _updc_mod.updc_transform
    _UPDCResult = _updc_mod.UPDCResult
except Exception:  # pragma: no cover - provide fallback implementation
    from dataclasses import dataclass
    from numbers import Real
    from typing import Dict

    @dataclass(frozen=True)
    class _UPDCResult:  # minimal replica of the engine's return type
        RT: float
        Q: float
        CI: float

    def _updc_transform(
        I: Real, S: Real, M: Real, W: Real, n: int, R: Real
    ) -> _UPDCResult:
        numeric_inputs: Dict[str, Real] = {"I": I, "S": S, "M": M, "W": W, "R": R}
        for name, value in numeric_inputs.items():
            if not isinstance(value, Real):
                raise TypeError(f"{name} must be a real number")
        if not isinstance(n, int):
            raise TypeError("n must be an integer")
        if n <= 0:
            raise ValueError("n must be a positive integer")
        denom = W + n
        if denom == 0:
            raise ValueError("W + n cannot be zero when computing RT")
        rt = (I + S + M) / denom
        q = R / n
        ci = 0.5 * (rt + q)
        return _UPDCResult(RT=float(rt), Q=float(q), CI=float(ci))


# ---------------------------------------------------------------------------
# Engine singletons

CONFIG_DIR = Path(os.getenv("SCORE_CONFIG_DIR", Path(__file__).parent / "config"))


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    data: Dict[str, Any] | None = None
    if yaml is not None:
        data = yaml.safe_load(text)  # type: ignore[assignment]
    else:  # pragma: no cover - minimal YAML parser
        data = {}
        for line in text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip()
    return data if isinstance(data, dict) else {}


class SpiceEngine:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg

    def score(self, scope: str, scope_id: str, window: list[str] | None):
        dsn = self.cfg.get("dsn")
        return _build_spice_report_v22(scope, scope_id, window, dsn=dsn)


class UPDCEngine:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg

    def score(self, params: Dict[str, Any]):
        result = _updc_transform(
            params["I"],
            params["S"],
            params["M"],
            params["W"],
            params["n"],
            params["R"],
        )
        return result


spice_engine = SpiceEngine(
    _load_yaml(Path(os.getenv("SPICE_ENGINE_CONFIG", CONFIG_DIR / "spice.yml")))
)
updc_engine = UPDCEngine(
    _load_yaml(Path(os.getenv("UPDC_ENGINE_CONFIG", CONFIG_DIR / "updc.yml")))
)

# ---------------------------------------------------------------------------
# Router

router = APIRouter(prefix="/score", tags=["score"], dependencies=[Depends(get_api_key)])


@router.post("/spice")
def score_spice(req: SpiceScope):
    try:
        return spice_engine.score(req.scope, req.scope_id, req.window)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/updc", response_model=UpdcOut)
def score_updc(req: UpdcIn):
    try:
        result = updc_engine.score(req.model_dump())
        return UpdcOut(RT=result.RT, Q=result.Q, CI=result.CI)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc))
