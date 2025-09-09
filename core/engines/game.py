"""Simple game theory utilities for strategy and payoff analysis.

This module implements a small normal–form game engine.  Games are defined by
their players, the strategies available to each player and a payoff matrix that
specifies the outcome for every strategy profile.  The engine provides a
best‑response solver that can be used to compute optimal strategies against a
fixed strategy profile of the opponents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

__all__ = ["Game"]


Strategy = str
Player = str
Profile = Tuple[Strategy, ...]
Payoff = Tuple[float, ...]


@dataclass
class Game:
    """Representation of a finite normal‑form game.

    Parameters
    ----------
    players:
        Ordered sequence of players participating in the game.
    strategies:
        Mapping from each player to the strategies available to them.
    payoffs:
        Mapping from strategy profiles to the corresponding payoff for each
        player.  A profile is a tuple of strategies ordered according to the
        ``players`` sequence.

    Notes
    -----
    The class performs minimal validation – it verifies that all players have
    strategies defined and that payoff entries match the number of players.
    """

    players: List[Player]
    strategies: Dict[Player, List[Strategy]]
    payoffs: Dict[Profile, Payoff]

    def __init__(
        self,
        players: Sequence[Player],
        strategies: Mapping[Player, Iterable[Strategy]],
        payoffs: Mapping[Sequence[Strategy], Sequence[float]],
    ) -> None:
        self.players = list(players)
        # Ensure that strategies are defined for all players
        if set(self.players) - set(strategies):
            missing = ", ".join(sorted(set(self.players) - set(strategies)))
            raise ValueError(f"missing strategies for players: {missing}")
        self.strategies = {p: list(strategies[p]) for p in self.players}

        # Normalise payoff mapping with tuple keys/values
        self.payoffs = {}
        for profile, payoff in payoffs.items():
            if len(profile) != len(self.players):
                raise ValueError("profile length does not match number of players")
            if len(payoff) != len(self.players):
                raise ValueError("payoff length does not match number of players")
            self.payoffs[tuple(profile)] = tuple(float(v) for v in payoff)

    def payoff(self, profile: Sequence[Strategy]) -> Payoff:
        """Return the payoff for a given strategy profile.

        Parameters
        ----------
        profile:
            Strategies for each player ordered according to :attr:`players`.

        Returns
        -------
        tuple of float
            Payoff for each player in the same order as ``profile``.
        """

        key = tuple(profile)
        if key not in self.payoffs:
            raise KeyError(f"unknown profile {profile}")
        return self.payoffs[key]

    def best_response(self, player: Player, opponents: Mapping[Player, Strategy]) -> List[Strategy]:
        """Compute a player's best responses to fixed opponent strategies.

        Parameters
        ----------
        player:
            Player for which to compute the best response.
        opponents:
            Mapping of all *other* players to the strategy they are assumed to
            play.

        Returns
        -------
        list of str
            Strategies that maximise the selected player's payoff.  Multiple
            strategies may be returned in case of ties.
        """

        if player not in self.players:
            raise KeyError(f"unknown player '{player}'")

        expected_opponents = set(self.players) - {player}
        if set(opponents) != expected_opponents:
            missing = ", ".join(sorted(expected_opponents - set(opponents)))
            extra = ", ".join(sorted(set(opponents) - expected_opponents))
            msg = []
            if missing:
                msg.append(f"missing strategies for: {missing}")
            if extra:
                msg.append(f"unexpected players: {extra}")
            raise ValueError("; ".join(msg))

        best: List[Strategy] = []
        best_value = float("-inf")

        for strategy in self.strategies[player]:
            profile: List[Strategy] = []
            for p in self.players:
                profile.append(strategy if p == player else opponents[p])
            value = self.payoff(profile)[self.players.index(player)]
            if value > best_value:
                best_value = value
                best = [strategy]
            elif value == best_value:
                best.append(strategy)

        return best

