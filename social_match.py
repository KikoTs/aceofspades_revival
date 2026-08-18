# -*- coding: utf-8 -*-
"""Ticketed handoff from a Revival social lobby to BattleSpades."""
from __future__ import absolute_import


def _show_error(menu, error, server_id=None):
    menu._social_join_inflight = False
    # The ticket minted for this endpoint is spent whether or not the join
    # succeeded, so the lobby must not silently retry the same address.
    marker = getattr(menu, "mark_social_server_failed", None)
    if callable(marker):
        try:
            marker(server_id)
        except Exception:
            pass
    try:
        from shared.constants import A968
        menu.manager.set_big_text_message(A968, False, 6.0)
    except Exception:
        pass
    try:
        print("Social match connection failed: %s" % error)
    except Exception:
        pass


def request_ticket(server_id, success, error=None):
    """Mint one join code for an endpoint that does not have to be listed yet.

    The master accepts this as soon as the relay allocation exists, so the
    host's ticket is fetched while its server is still booting instead of after
    the public listing round-trip.
    """
    if not server_id:
        return False
    try:
        from shared.steam import SteamRequestSocialGameTicket
        return bool(SteamRequestSocialGameTicket(server_id, success, error))
    except Exception as caught:
        if callable(error):
            error(caught)
        return False


def connect(menu, server_id, local_identifier=None, previous_menu=None,
            success_callback=None, error_callback=None, ticket=None):
    """Enter LoadingMenu exactly once with a one-use ticket for ``server_id``."""
    if not server_id or getattr(menu, "_social_join_inflight", False):
        return False
    menu._social_join_inflight = True

    def failed(error):
        _show_error(menu, error, server_id)
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
            from shared.constants import SERVERMODE_CUSTOM
            parent.set_menu(
                LoadingMenu,
                identifier=identifier,
                # A player-hosted match is a custom server.  Announcing it as
                # SERVERMODE_PUBLIC makes the retail client apply its public
                # matchmaking rules and refuse the join with "to connect to a
                # ranked server, use the Ranked Match option".
                server_mode=SERVERMODE_CUSTOM,
                from_server_menu=True,
                name="Revival Match",
                previous_menu=previous_menu or type(menu),
            )
            menu._social_join_inflight = False
            if callable(success_callback):
                success_callback(ticket)
        except Exception as error:
            failed(error)

    if ticket is not None:
        # Already minted while the server was booting.
        ticket_ready(ticket)
        return True

    if not request_ticket(server_id, ticket_ready, failed):
        failed(RuntimeError("The social service is unavailable."))
        return False
    return True


__all__ = ["connect"]
