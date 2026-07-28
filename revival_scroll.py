# -*- coding: utf-8 -*-
"""Stable mouse-wheel step handling for the legacy Pyglet 1.2 client."""
from __future__ import division


_REMAINDER_ATTRIBUTE = "_revival_wheel_remainder"
_FLOAT_EPSILON = 1e-9


def consume_wheel_steps(target, delta):
    """Return complete wheel steps while retaining high-resolution fractions.

    Pyglet 1.2 exposes Windows wheel input as multiples or fractions of one
    physical notch. Precision devices can therefore emit several small values
    for one gesture. Accumulating those values prevents every partial packet
    from becoming a separate menu-row jump.
    """

    try:
        delta = float(delta)
    except (TypeError, ValueError):
        return 0
    if delta == 0.0 or delta != delta:
        return 0

    remainder = float(getattr(target, _REMAINDER_ATTRIBUTE, 0.0))
    if remainder and (remainder > 0.0) != (delta > 0.0):
        remainder = 0.0

    total = remainder + delta
    magnitude = int(abs(total) + _FLOAT_EPSILON)
    if magnitude == 0:
        setattr(target, _REMAINDER_ATTRIBUTE, total)
        return 0

    steps = magnitude if total > 0.0 else -magnitude
    remainder = total - steps
    if abs(remainder) < _FLOAT_EPSILON:
        remainder = 0.0
    setattr(target, _REMAINDER_ATTRIBUTE, remainder)
    return steps
