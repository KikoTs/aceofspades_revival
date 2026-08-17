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
    return True


def active(manager):
    with _lock:
        return manager is not None and id(manager) in _active


__all__ = ["activate", "restore", "active"]
