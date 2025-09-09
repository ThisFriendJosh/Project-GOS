import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.engines.game import Game


def _prisoners_dilemma() -> Game:
    """Create a classic Prisoner's Dilemma game instance."""

    players = ["Alice", "Bob"]
    strategies = {"Alice": ["C", "D"], "Bob": ["C", "D"]}
    payoffs = {
        ("C", "C"): (-1, -1),
        ("C", "D"): (-3, 0),
        ("D", "C"): (0, -3),
        ("D", "D"): (-2, -2),
    }
    return Game(players, strategies, payoffs)


def test_payoff_calculation() -> None:
    game = _prisoners_dilemma()
    assert game.payoff(("C", "D")) == (-3, 0)


def test_best_response() -> None:
    game = _prisoners_dilemma()
    assert game.best_response("Alice", {"Bob": "C"}) == ["D"]
    assert game.best_response("Bob", {"Alice": "D"}) == ["D"]


def test_best_response_ties() -> None:
    players = ["P1", "P2"]
    strategies = {"P1": ["A", "B"], "P2": ["X"]}
    payoffs = {("A", "X"): (1, 0), ("B", "X"): (1, 0)}
    game = Game(players, strategies, payoffs)
    assert set(game.best_response("P1", {"P2": "X"})) == {"A", "B"}

