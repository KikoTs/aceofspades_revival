from aoslib.scenes.frontend.baseSquadsMenu import *
from shared.steam import SteamEnumerateFriendLobbies, SteamEnumeratePublicLobbies, SteamGetLobbyMembers, SteamCreateLobby, SteamJoinLobby, SteamSetLobbyData, SteamGetPersonaName, SteamLeaveLobby, SteamRefreshLobbyData, SteamGetLobbyData, SteamActivateGameOverlayToStore, GetUserSteamID, SteamAmITheLobbyOwner
from shared.constants import ERROR_LOBBY_CONNECTION_FAILED
from shared.constants_matchmaking import A2663
from shared.constants_prefabs import A3055, A3037
import playlists, time
from aoslib.scenes.main.matchSettings import generate_ugc_map_title
from shared.steam import game_version

class UGCSquadsMenu(BaseSquadsMenu):
    lobbyType = A2663
    title = strings.UGC_SQUADS_MENU_TITLE
    create_button_text = strings.UGC_SQUADS_MENU_CREATE
    join_button_text = strings.UGC_SQUADS_MENU_JOIN
    create_button_text = strings.UGC_SQUADS_MENU_NEW_LOBBY
    available_lobbies_text = strings.UGC_OPEN_LOBBIES
    move_to_lobby = False

    def on_lobby_join_success(self, lobby_id):
        from aoslib.scenes.frontend.ugcSquadLobbyMenu import UGCSquadLobbyMenu
        self.parent.set_menu(UGCSquadLobbyMenu)

    def lobby_created_callback(self, lobby_id):
        if not SteamAmITheLobbyOwner():
            return
        else:
            SteamSetLobbyData('Name', SteamGetPersonaName())
            SteamSetLobbyData('Version', str(game_version()))
            SteamSetLobbyData('LobbyType', str(self.lobbyType))
            SteamSetLobbyData('LobbyCreator', str(SteamGetLobbyOwner()))
            playlist = playlists.get_mode_playlist('ugc')
            if playlist is not None:
                game_rules = ''
                map_name = sorted(playlist.map_names)[0]
                SteamSetLobbyData('PlaylistID', str(playlist.id))
                SteamSetLobbyData('PLAYLIST', str(playlist.modes[0]))
                SteamSetLobbyData('UGC_MODES', str(playlist.ugc_modes[0]))
                map_rotation = map_name
                map_name = strings.get_by_id(map_rotation)
                new_title = generate_ugc_map_title(map_name)
                SteamSetLobbyData('MAP_ROTATION_ORIGINAL_TITLE', map_name)
                SteamSetLobbyData('MAP_ROTATION_FILENAME', map_rotation)
                SteamSetLobbyData('MAP_ROTATION_NEW_TITLE', new_title)
                SteamSetLobbyData('Custom_UGC_Map', 'False')
                prefabs = A3037
                map = map_name.lower()
                if map in A3055:
                    prefab_sets = A3055[map]
                    if len(prefab_sets) > 0:
                        prefabs = prefab_sets[0]
                SteamSetLobbyData('PREFAB_SET', str(prefabs))
                teams = [
                 'TEAM1', 'TEAM2']
                for team in teams:
                    SteamSetLobbyData(team, '0')

                SteamSetLobbyData('TEAM_NEUTRAL', '1')
                reset_all_game_rules()
            SteamSetLobbyData('MATCH_LENGTH', str(0))
            SteamSetLobbyData('MAX_PLAYERS', str(playlist.players[0]))
            self.manager.hosted_ugc_map_filename = ''
            time.sleep(0.1)
            self.move_to_lobby = True
            return

    def lobby_create_error_callback(self, reason):
        self.manager.set_big_text_message(ERROR_LOBBY_CONNECTION_FAILED, False, 5.0)

    def update(self, dt):
        super(UGCSquadsMenu, self).update(dt)
        if self.move_to_lobby:
            self.move_to_lobby = False
            from aoslib.scenes.frontend.ugcSquadLobbyMenu import UGCSquadLobbyMenu
            self.parent.set_menu(UGCSquadLobbyMenu)

    def open_parent_menu(self):
        from aoslib.scenes.frontend.ugcSelectMenu import UGCSelectMenu
        self.manager.set_menu(UGCSelectMenu, back=True)
