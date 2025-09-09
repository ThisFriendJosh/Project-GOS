"""Engine modules exposed at :mod:`core.engines`.

This package provides stub implementations of various analytical engines.  The
modules are kept lightweight to ensure that importing ``core.engines`` works in
minimal testing environments.
"""

from . import catma, game

__all__ = ["catma", "game"]
