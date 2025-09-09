"""Ensure engine modules can be imported via the ``core.engines`` package."""

import importlib


def test_engine_modules_importable() -> None:
    """All known engine modules should be importable through ``core.engines``."""
    # Import the package first to verify it is a regular package.
    from core import engines

    assert importlib.import_module("core.engines.catma") is engines.catma
    assert importlib.import_module("core.engines.game") is engines.game
    assert importlib.import_module("core.engines.updc") is engines.updc
