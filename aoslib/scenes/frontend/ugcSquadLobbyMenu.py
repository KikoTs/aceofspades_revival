from aoslib.scenes.frontend.baseSquadLobbyMenu import *
from shared.steam import SteamGetLobbyMembers, SteamGetCurrentLobby, SteamGetFriendPersonaName, SteamGetPersonaName, SteamShowInviteFriendOverlay, SteamLeaveLobby, SteamGetLobbyOwner, SteamAmITheLobbyOwner, SteamSetLobbyData, SteamSetLobbyMemberData, SteamGetLobbyData, SteamGetLobbyMemberData, SteamSendChatMessage, SteamSetLobbyGameServer, SteamGetLobbyGameServer, SteamClearLobbyGameServer, GetUserSteamID, SteamGetLobbyOwner

class UGCSquadLobbyMenu(BaseSquadLobbyMenu):
    title = strings.UGC_SQUADS_LOBBY_TITLE
    settings_title = strings.UGC_SETTINGS

    def initialize(self, ugc_mode=True):
        super(UGCSquadLobbyMenu, self).initialize(ugc_mode)

    def on_start(self, *arg, **kw):
        super(UGCSquadLobbyMenu, self).on_start(arg, kw)
        self.match_settings_panel.enable_privacy_type = True
        self.match_settings_panel.enable_match_length = False
        self.match_settings_panel.enable_game_rules = False
        self.match_settings_panel.enable_map_rotation = True
        self.match_settings_panel.enable_max_players = True
        self.match_settings_panel.enable_playlist = False
        self.match_settings_panel.enable_ugc_mode = True
        self.match_settings_panel.enable_save_map_name = True
        self.match_settings_panel.enable_prefab_set = True
        self.match_settings_panel.populate_match_settings_list()
        self.update_team_id_on_playlist_selected(False, False, True)
        host_id = SteamGetLobbyData(SteamGetCurrentLobby(), 'LobbyCreator')
        if str(SteamGetLobbyOwner()) != host_id:
            self.open_parent_menu()

    def open_parent_menu(self):
        if SteamAmITheLobbyOwner():
            self.on_cancel_game()
        SteamLeaveLobby()
        self.lobby_id = None
        from ugcSquadsMenu import UGCSquadsMenu
        self.parent.set_menu(UGCSquadsMenu, back=True)
        return

    def on_user_left(self, friend_id, kicked=False):
        super(UGCSquadLobbyMenu, self).on_user_left(friend_id)
        host_id = SteamGetLobbyData(SteamGetCurrentLobby(), 'LobbyCreator')
        if str(SteamGetLobbyOwner()) != host_id:
            self.open_parent_menu()
