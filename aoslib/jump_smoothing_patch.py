# -*- coding: utf-8 -*-
"""Smooth retail jump launches and rejected block-edge corrections."""
from __future__ import division

import os


MAX_LAUNCH_RESTORE_DISTANCE = 0.25
MAX_LAUNCH_RESTORE_DISTANCE_SQ = MAX_LAUNCH_RESTORE_DISTANCE ** 2
ACCEPTED_JUMP_VELOCITY_Z = -0.2


def _position3(value):
    """Return a native vector-like value as an immutable XYZ tuple."""

    return (float(value[0]), float(value[1]), float(value[2]))


def _accepted_jump(world_object):
    """Return whether native physics produced the retail launch impulse."""

    return bool(
        world_object.airborne
        and float(world_object.velocity[2]) < ACCEPTED_JUMP_VELOCITY_Z
    )


def install():
    """Install one idempotent guard around the native Character update."""

    if os.environ.get("AOS_DISABLE_CHARACTER_JUMP_SMOOTHING") == "1":
        return False

    from aoslib.character import Character

    if getattr(Character, "_jump_anchor_smoothing_installed", False):
        return True

    original_update = Character.update

    def smoothed_update(self, *args, **kwargs):
        world_object = getattr(self, "world_object", None)
        if world_object is None:
            return original_update(self, *args, **kwargs)

        before_position = _position3(world_object.position)
        before_velocity = _position3(world_object.velocity)
        was_airborne = bool(world_object.airborne)
        result = original_update(self, *args, **kwargs)

        attempted_jump = bool(
            not was_airborne and bool(world_object.jump_this_frame)
        )
        accepted_jump = attempted_jump and _accepted_jump(world_object)
        rejected_jump = attempted_jump and not accepted_jump
        if accepted_jump or rejected_jump:
            after_position = _position3(world_object.position)
            displacement_sq = sum(
                (after_position[index] - before_position[index]) ** 2
                for index in range(3)
            )
            if displacement_sq > MAX_LAUNCH_RESTORE_DISTANCE_SQ:
                if accepted_jump:
                    world_object.set_position(*before_position)
                elif (
                    (after_position[0] - before_position[0]) * before_velocity[0]
                    + (after_position[1] - before_position[1]) * before_velocity[1]
                    < 0.0
                ):
                    # A rejected jump against a one-block edge can restore a
                    # stale owner row and snap backward. Preserve the native
                    # vertical correction while cancelling only that rollback.
                    world_object.set_position(
                        before_position[0],
                        before_position[1],
                        after_position[2],
                    )
        return result

    Character._jump_anchor_smoothing_original_update = original_update
    Character.update = smoothed_update
    Character._jump_anchor_smoothing_installed = True
    return True
