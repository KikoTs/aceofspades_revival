# -*- coding: utf-8 -*-
"""Shared navigation into an authoritative Revival social lobby."""
from __future__ import absolute_import

from shared.constants_matchmaking import A2663
from shared.steam import SteamGetCurrentLobby, SteamGetLobbyData


def social_lobby_menu_class(lobby_id=None):
    lobby_id = int(lobby_id or SteamGetCurrentLobby() or 0)
    lobby_type = SteamGetLobbyData(lobby_id, "LobbyType") if lobby_id else ""
    if lobby_type == str(A2663):
        from aoslib.scenes.frontend.ugcSquadLobbyMenu import UGCSquadLobbyMenu
        return UGCSquadLobbyMenu
    from aoslib.scenes.frontend.matchSquadLobbyMenu import MatchSquadLobbyMenu
    return MatchSquadLobbyMenu


def open_social_lobby(manager, parent=None, as_scene=False, back=False):
    lobby_id = SteamGetCurrentLobby()
    if not lobby_id:
        return False
    menu_class = social_lobby_menu_class(lobby_id)
    if as_scene:
        from aoslib.scenes.frontend.menuScene import MenuScene as FrontendMenuScene
        manager.set_scene(FrontendMenuScene, menu=menu_class)
    elif parent is not None:
        parent.set_menu(menu_class, back=back, in_game_menu=False)
    else:
        manager.set_menu(menu_class, in_game_menu=False)
    return True


__all__ = ["open_social_lobby", "social_lobby_menu_class"]
