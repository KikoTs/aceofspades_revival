# -*- coding: utf-8 -*-
"""Ticketed handoff from a Revival social lobby to BattleSpades."""
from __future__ import absolute_import


def _show_error(menu, error):
    menu._social_join_inflight = False
    try:
        from shared.constants import A968
        menu.manager.set_big_text_message(A968, False, 6.0)
    except Exception:
        pass
    try:
        print("Social match connection failed: %s" % error)
    except Exception:
        pass


def connect(menu, server_id, local_identifier=None, previous_menu=None,
            success_callback=None, error_callback=None):
    """Request a fresh one-use ticket and enter LoadingMenu exactly once."""
    if not server_id or getattr(menu, "_social_join_inflight", False):
        return False
    menu._social_join_inflight = True

    def failed(error):
        _show_error(menu, error)
        if callable(error_callback):
            error_callback(error)

    def ticket_ready(ticket):
        try:
            import revival_wire_identity
            from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
            if not revival_wire_identity.activate(menu.manager, ticket):
                raise RuntimeError("The temporary join identity could not be activated.")
            identifier = local_identifier or server_id
            parent = getattr(menu, "parent", None)
            if parent is None or not hasattr(parent, "set_menu"):
                revival_wire_identity.restore(menu.manager)
                raise RuntimeError("The lobby has no loading-menu transition parent.")
            try:
                from shared.steam import SteamSetLobbyMemberData
                SteamSetLobbyMemberData("in-game", "1")
            except Exception:
                pass
            parent.set_menu(
                LoadingMenu,
                identifier=identifier,
                from_server_menu=True,
                name="Revival Match",
                previous_menu=previous_menu or type(menu),
            )
            menu._social_join_inflight = False
            if callable(success_callback):
                success_callback(ticket)
        except Exception as error:
            failed(error)

    try:
        from shared.steam import SteamRequestSocialGameTicket
        if not SteamRequestSocialGameTicket(server_id, ticket_ready, failed):
            failed(RuntimeError("The social service is unavailable."))
            return False
    except Exception as error:
        failed(error)
        return False
    return True


__all__ = ["connect"]
