"""Simple simulation loop for campaign reach.

This module provides :func:`predict_policy_impact` which performs a very
small agent-based style simulation.  The goal of the function is not to be a
fully fledged simulator but rather a deterministic toy model that the tests
can exercise.

The model tracks an abstract ``reach`` value for a campaign.  ``reach`` starts
at a baseline value and is modified on each tick by two configurable
parameters:

``network``
    Represents the strength of network effects.  The higher the value, the
    more the current reach grows due to sharing.

``decay``
    Models saturation or audience loss between ticks.

Both parameters are multiplied by the share/amplify scalars supplied by the
caller so that tests can easily tweak scenarios.
"""


def predict_policy_impact(
    campaign_id,  # type: ignore[unused-argument]
    s_amp=None,
    s_share=None,
    network: float = 0.0,
    decay: float = 0.0,
    ticks: int = 10,
    dsn=None,  # type: ignore[unused-argument]
):
    """Evolve a campaign for a number of ticks.

    The function returns a dictionary containing the trajectory of the reach
    as well as the final ``projected_reach`` after ``ticks`` iterations.  All
    parameters default to no change so that the baseline is a flat line.
    """

    base = 1000
    amp = s_amp if s_amp is not None else 1.0
    shr = s_share if s_share is not None else 1.0

    reach = base * amp
    trajectory = [int(reach)]

    for _ in range(ticks):
        # Apply network effects and decay at each tick.  Casting to ``float``
        # ensures any callers using ``Decimal`` or other numeric types behave
        # predictably.
        reach = float(reach) * (1 + network * shr)
        reach *= 1 - decay
        trajectory.append(int(reach))

    return {
        "baseline_reach": base,
        "projected_reach": trajectory[-1],
        "trajectory": trajectory,
        "params": {
            "amplify": amp,
            "share": shr,
            "network": network,
            "decay": decay,
            "ticks": ticks,
        },
    }


