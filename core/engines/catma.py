r"""CATMA engine.

This module provides small utilities to model *machines* (finite state
machines), evaluate a policy :math:`\eta` on those machines and perform basic
path mathematics.  The goal is not to be feature complete but to supply the
minimal capabilities needed by the tests in this kata.

The public API intentionally mirrors common terminology used in the project::

    >>> m = Machine(start="A", transitions={"A": {"x": "B"}, "B": {}})
    >>> def policy(state, action):
    ...     return 0.5
    >>> evaluate_path(m, ["x"], policy)
    0.5

The functions are small but well documented and type hinted to make them easy
to reason about during experimentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple


# ---------------------------------------------------------------------------
# Types

Policy = Callable[[str, str], float]
r"""Callable describing the policy :math:`\eta`.

The callable receives the current ``state`` and an ``action`` and must return
the weight/probability for taking that action.  The return value is multiplied
across a path when evaluating it.
"""


# ---------------------------------------------------------------------------
# Machine definition


@dataclass
class Machine:
    """Simple finite state machine.

    Parameters
    ----------
    start:
        The name of the starting state.
    transitions:
        Nested mapping of ``state -> action -> next_state``.

    Only the functionality needed by the tests is implemented: stepping
    through transitions and walking a sequence of actions.
    """

    start: str
    transitions: Dict[str, Dict[str, str]]

    # --- helper methods -------------------------------------------------

    def step(self, state: str, action: str) -> str:
        """Return the next state when performing ``action`` from ``state``.

        Raises
        ------
        KeyError
            If the state or action is unknown.
        """

        try:
            return self.transitions[state][action]
        except KeyError as exc:  # pragma: no cover - simple error wrapping
            raise KeyError(f"No transition defined for state {state!r} and action {action!r}") from exc

    def walk(self, actions: Iterable[str]) -> List[str]:
        """Traverse the machine following ``actions``.

        Returns a list of visited states including the start state.
        """

        state = self.start
        path = [state]
        for action in actions:
            state = self.step(state, action)
            path.append(state)
        return path


# ---------------------------------------------------------------------------
# Policy / path mathematics


def evaluate_path(machine: Machine, actions: Iterable[str], policy: Policy) -> float:
    """Evaluate a path's value under ``policy``.

    ``policy`` is called for each ``(state, action)`` pair and the returned
    weights are multiplied across the path.  The final product is returned.
    """

    value = 1.0
    state = machine.start
    for action in actions:
        weight = policy(state, action)
        value *= weight
        state = machine.step(state, action)
    return value


def enumerate_paths(machine: Machine, depth: int) -> List[List[str]]:
    """Enumerate all state paths up to ``depth`` transitions.

    The returned list contains paths represented as lists of states.  The start
    state itself is included as a path of length ``0``.
    """

    paths: List[List[str]] = []

    def dfs(state: str, path: List[str], remaining: int) -> None:
        paths.append(path.copy())
        if remaining == 0:
            return
        for _action, nxt in machine.transitions.get(state, {}).items():
            dfs(nxt, path + [nxt], remaining - 1)

    dfs(machine.start, [machine.start], depth)
    return paths


def best_path(machine: Machine, depth: int, policy: Policy) -> Tuple[List[str], float]:
    """Return the path (up to ``depth`` transitions) with the highest value.

    The evaluation uses ``policy`` in the same way as :func:`evaluate_path`.

    Returns
    -------
    tuple
        A ``(path, value)`` pair where ``path`` is the list of states and
        ``value`` is the cumulative policy value for that path.
    """

    # Start with an impossible value to ensure any real path replaces it.
    best: Tuple[List[str], float] = ([], float("-inf"))

    def dfs(state: str, path: List[str], value: float, remaining: int) -> None:
        nonlocal best
        # Evaluate paths that either exhausted the depth or reached a leaf node
        if remaining == 0 or not machine.transitions.get(state):
            if value > best[1]:
                best = (path.copy(), value)
        if remaining == 0:
            return
        for action, nxt in machine.transitions.get(state, {}).items():
            weight = policy(state, action)
            dfs(nxt, path + [nxt], value * weight, remaining - 1)

    dfs(machine.start, [machine.start], 1.0, depth)
    if best[0]:
        return best
    # No transitions were explored; return start state with neutral value
    return [machine.start], 1.0


__all__ = [
    "Machine",
    "Policy",
    "evaluate_path",
    "enumerate_paths",
    "best_path",
]

