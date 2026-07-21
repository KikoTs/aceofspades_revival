# -*- coding: utf-8 -*-
"""Move a retained BattleSpades connection into the retail map loader.

The stock MapEnded handler freezes GameScene but never opens LoadingMenu.
BattleSpades deliberately keeps the authenticated ENet peer during a map or
mode change, so this hook installs LoadingMenu and acknowledges that the
crash-sensitive InitialInfo packet can now be consumed safely.

The hook wraps the GameManager's existing scheduled update callback. It is
Python 2 compatible and performs no polling thread, filesystem I/O, or network
work beyond one existing reliable ClientInMenu packet per transition.
"""
from __future__ import absolute_import, print_function

import sys


_installed = False
_transition_scene = None
_transition_ready_sent = False


def _manager_from_callback(callback):
    owner = getattr(callback, 'im_self', None)
    if owner is None:
        owner = getattr(callback, '__self__', None)
    if owner is None:
        owner = getattr(sys, '_aos_manager', None)
    if owner is None or type(owner).__name__ != 'GameManager':
        return None
    return owner


def _enter_loading_menu(manager):
    """Open and acknowledge the same-connection loader once per map epoch."""
    global _transition_scene, _transition_ready_sent

    scene = getattr(manager, 'game_scene', None)
    client = getattr(manager, 'client', None)
    if scene is None or client is None or getattr(client, 'disconnected', True):
        _transition_scene = None
        _transition_ready_sent = False
        return

    ended = (
        bool(getattr(scene, 'pause_players', False))
        and bool(getattr(scene, 'pause_entities', False))
        and bool(getattr(scene, 'pause_particles', False))
    )
    if not ended:
        # GameScene is a manager-owned singleton. Its native pause flags, not
        # object identity, delimit consecutive map epochs.
        _transition_scene = None
        _transition_ready_sent = False
        return

    if _transition_scene is not scene:
        try:
            from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
            # identifier=None reuses the current GameClient/ENet peer.
            manager.set_menu(LoadingMenu, from_server_menu=False)
            _transition_scene = scene
            _transition_ready_sent = False
        except Exception:
            _transition_scene = None
            try:
                import traceback
                traceback.print_exc()
            except Exception:
                pass
            return

    if _transition_ready_sent:
        return
    try:
        from shared.packet import ClientInMenu
        ready = ClientInMenu()
        ready.in_menu = 1
        client.send_packet(ready)
        _transition_ready_sent = True
    except Exception:
        # Keep LoadingMenu installed and retry the acknowledgement next frame.
        try:
            import traceback
            traceback.print_exc()
        except Exception:
            pass


def install():
    """Install before aoslib.run schedules GameManager.update."""
    global _installed
    if _installed:
        return True

    try:
        import pyglet.clock as clock
    except Exception:
        return False

    original = getattr(clock, 'schedule_interval_soft', None)
    if original is None:
        return False

    def schedule_interval_soft(callback, interval, *args, **kwargs):
        manager = _manager_from_callback(callback)
        if manager is None:
            return original(callback, interval, *args, **kwargs)

        def transition_aware_update(dt, *update_args, **update_kwargs):
            result = callback(dt, *update_args, **update_kwargs)
            _enter_loading_menu(manager)
            return result

        return original(
            transition_aware_update,
            interval,
            *args,
            **kwargs
        )

    clock.schedule_interval_soft = schedule_interval_soft
    _installed = True
    return True


install()
