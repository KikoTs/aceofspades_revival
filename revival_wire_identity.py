# -*- coding: utf-8 -*-
"""Temporary Protocol 168 wire-name override for one-use Revival tickets."""
from __future__ import absolute_import

import threading


_lock = threading.RLock()
_active = {}

try:
    text_type = unicode
except NameError:
    text_type = str


def _set_wire_name(value):
    """Drive the name the game sends on the wire, if this ABI has it."""
    try:
        from shared.steam import SteamSetWireNameOverride
    except ImportError:
        return False
    try:
        return bool(SteamSetWireNameOverride(value))
    except Exception:
        return False


def activate(manager, join_code):
    """Use an ASCII join code only until the server accepts world startup."""
    if manager is None or not isinstance(join_code, (str, text_type)):
        return False
    try:
        join_code = join_code.encode("ascii") if text_type is not str else join_code
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False
    if not join_code.startswith("~") or len(join_code) != 15:
        return False
    config = getattr(manager, "config", None)
    if config is None or not hasattr(config, "name"):
        return False
    key = id(manager)
    with _lock:
        if key not in _active:
            _active[key] = (manager, config.name)
        config.name = join_code
    # The name the game actually puts in NewPlayerConnection comes from
    # SteamGetPersonaName, not from the client config, so the config alone
    # never reached the server.  An identity-required match refuses any name
    # that is not a join code, which the client reports as "to connect to a
    # ranked server, use the Ranked Match option".
    _set_wire_name(join_code)
    return True


def restore(manager):
    """Restore the visible Revival nickname; idempotent on every exit path."""
    if manager is None:
        return False
    with _lock:
        record = _active.pop(id(manager), None)
    if record is None:
        return False
    _, original_name = record
    config = getattr(manager, "config", None)
    if config is not None and hasattr(config, "name"):
        config.name = original_name
    _set_wire_name(u"")
    return True


def active(manager):
    with _lock:
        return manager is not None and id(manager) in _active


def _player_is_in_the_world(manager):
    scene = getattr(manager, "game_scene", None)
    player = getattr(scene, "player", None)
    if player is None:
        return False
    try:
        return int(getattr(player, "id", -1)) >= 0
    except (TypeError, ValueError):
        return False


def restore_when_accepted(manager, timeout=120.0):
    """Hold the join code until the server has actually accepted the player.

    The client does not send ``NewPlayerConnection`` -- the only packet that
    carries the name -- until a class is confirmed, which is several menus after
    ``InitialInfo``.  Restoring the nickname on ``InitialInfo`` therefore handed
    the server an unverified name, and an identity-required match answers that
    by disconnecting with the reason the client renders as "to connect to a
    ranked server, use the Ranked Match option".
    """

    if manager is None or not active(manager):
        return False
    try:
        from pyglet import clock
    except ImportError:
        restore(manager)
        return False

    deadline = [None]

    def poll(_dt):
        if deadline[0] is None:
            deadline[0] = _now() + timeout
        if not active(manager):
            clock.unschedule(poll)
            return
        if _player_is_in_the_world(manager) or _now() >= deadline[0]:
            clock.unschedule(poll)
            restore(manager)

    clock.schedule_interval(poll, 0.25)
    return True


def _now():
    import time
    return time.time()


__all__ = ["activate", "restore", "active", "restore_when_accepted"]
