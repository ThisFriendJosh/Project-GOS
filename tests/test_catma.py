"""Tests for the CATMA engine."""

import sys
from pathlib import Path

import pytest


# Make the repository importable when running the tests directly from the
# checked-out sources.  This mirrors the style of other tests in the project.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.engines.catma import Machine, evaluate_path, enumerate_paths, best_path


def _machine() -> Machine:
    """Return a small example machine used throughout the tests."""

    transitions = {
        "A": {"x": "B", "z": "C"},
        "B": {"y": "C"},
        "C": {},
    }
    return Machine(start="A", transitions=transitions)


def _policy(state: str, action: str) -> float:
    """Example policy providing weights for each transition."""

    weights = {("A", "x"): 0.6, ("A", "z"): 0.4, ("B", "y"): 0.5}
    return weights.get((state, action), 0.0)


def test_walk_and_evaluate():
    machine = _machine()
    actions = ["x", "y"]

    assert machine.walk(actions) == ["A", "B", "C"]
    value = evaluate_path(machine, actions, _policy)
    assert value == pytest.approx(0.6 * 0.5)


def test_enumerate_paths():
    machine = _machine()
    paths = enumerate_paths(machine, depth=2)

    # Expected paths (state sequences) up to two transitions
    assert ["A"] in paths
    assert ["A", "B"] in paths
    assert ["A", "C"] in paths
    assert ["A", "B", "C"] in paths
    assert len(paths) == 4


def test_best_path():
    machine = _machine()
    path, value = best_path(machine, depth=2, policy=_policy)

    assert path == ["A", "C"]
    # This path uses transition ('A','z') with weight 0.4
    assert value == pytest.approx(0.4)

