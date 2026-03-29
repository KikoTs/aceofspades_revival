from aoslib.scenes.frontend.lobbyPanelBase import LobbyPanelBase
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.frontend.panelBase import BACKGROUND_NONE
from aoslib.scenes.frontend.playlistUIManager import PlayListUIManager
from aoslib.scenes.main.matchSettings import get_list_items_as_string, get_game_info_data, get_string_as_list, get_default_match_length_for_playlist_in_minutes, get_playlist_with_id, get_default_playlist
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from shared.constants_gamemode import A2450
from shared.steam import SteamSetLobbyData, SteamGetCurrentLobby, SteamGetLobbyData, SteamAmITheLobbyOwner
from shared.constants_matchmaking import A2667

class PlayListPanel(LobbyPanelBase):

    def __init__(self, manager, ugc_mode=False):
        self.ugc_mode = ugc_mode
        super(PlayListPanel, self).__init__(manager)

    def initialize(self):
        super(PlayListPanel, self).initialize()
        self.list_panel = ListPanelBase(self.manager)
        self.playlistManager = PlayListUIManager(self.list_panel, False, False, ugc_mode=self.ugc_mode)
        self.on_playlist_selected_callback = None
        return

    def initialise_ui(self, lobby_id, x, y, width, height):
        super(PlayListPanel, self).initialise_ui(lobby_id, x, y, width, height)
        self.selected_server_type = None
        self.list_panel.initialise_ui(strings.CHOOSE_GAME_MODE, x, y, width, height, has_header=True)
        self.list_panel.set_background(BACKGROUND_NONE)
        self.list_panel.center_header_text = True
        self.list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        self.elements.append(self.list_panel)
        self.__initialise()
        return

    def close(self):
        for row in [row for row in self.list_panel.rows if hasattr(row, 'close')]:
            row.close()

        return super(PlayListPanel, self).close()

    def __initialise(self):
        self.playlistManager.populate_playlist()
        self.set_last_selected_row(silent=True)

    def set_content_visibility(self, visible):
        if self.visible_content == visible:
            return
        else:
            if SteamAmITheLobbyOwner():
                if visible:
                    self.__initialise()
                elif self.playlistManager is not None:
                    self.playlistManager.save_selected_row()
                    row = self.list_panel.get_selected_item()
                    if row is not None and len(row.modes) > 0:
                        modes_string = get_list_items_as_string(row.modes)
                        maps_string = get_list_items_as_string(row.map_rotation)
                        SteamSetLobbyData('PlaylistID', str(row.id))
                        SteamSetLobbyData('PLAYLIST', modes_string)
                        self.clear_other_modes_rules(row.modes)
                    self.playlistManager.selected_row = row
                self.list_panel.enabled = visible
            super(PlayListPanel, self).set_content_visibility(visible)
            return

    def clear_other_modes_rules(self, current_modes):
        for mode_id in A2450.keys():
            if mode_id in current_modes or mode_id not in A2667.keys():
                continue
            current_mode_rules = []
            for mode in current_modes:
                current_mode_rules += A2667[mode]

            for rule_id in A2667[mode_id]:
                if rule_id not in current_mode_rules:
                    SteamSetLobbyData(rule_id, '')

    def on_row_selected(self, index, row):
        if row is None or self.playlistManager is None:
            return
        self.playlistManager.on_row_selected(index, row)
        self.update_lobby_data(row.id, row.server_type, row.map_rotation, row.modes)
        if self.on_playlist_selected_callback is not None:
            draw_team_selection_box = 'ugc' not in row.modes
            enable_team_assignment = 'zom' not in row.modes and 'ugc' not in row.modes
            enable_kick_button = 'ugc' in row.modes and not enable_team_assignment
            self.on_playlist_selected_callback(draw_team_selection_box, enable_team_assignment, enable_kick_button)
        return

    def check_map_is_valid(self, playlist_id):
        if not SteamAmITheLobbyOwner():
            return
        else:
            playlist = get_playlist_with_id(int(playlist_id))
            if playlist is None:
                return
            current_map = SteamGetLobbyData(self.lobby_id, 'MAP_ROTATION_FILENAME')
            custom_ugc_map = SteamGetLobbyData(self.lobby_id, 'Custom_UGC_Map')
            if not self.playlistManager.is_map_valid_for_playlist(current_map, custom_ugc_map, playlist):
                default_map_for_new_playlist = sorted(playlist.map_names)[0]
                SteamSetLobbyData('MAP_ROTATION_FILENAME', default_map_for_new_playlist)
                SteamSetLobbyData('MAP_ROTATION_ORIGINAL_TITLE', default_map_for_new_playlist)
                SteamSetLobbyData('MAP_ROTATION_NEW_TITLE', default_map_for_new_playlist)
            return

    def update_lobby_data(self, playlist_id, server_type, map_rotation, map_modes, set_default=False):
        if not SteamAmITheLobbyOwner():
            return
        else:
            map_modes_string = get_list_items_as_string(map_modes)
            SteamSetLobbyData('PlaylistID', str(playlist_id))
            SteamSetLobbyData('PLAYLIST', map_modes_string)
            playlist = get_playlist_with_id(playlist_id)
            if playlist is not None:
                for default_rule, default_value in playlist.config.iteritems():
                    SteamSetLobbyData(default_rule, default_value)

            self.check_map_is_valid(playlist_id)
            return

    def set_last_selected_row(self, random_item=None, silent=False):
        if self.playlistManager is None:
            return
        else:
            default_id = SteamGetLobbyData(SteamGetCurrentLobby(), 'PlaylistID')
            for row in self.list_panel.rows:
                if str(row.id) == default_id:
                    self.playlistManager.selected_row = row
                    break

            if self.playlistManager.selected_row is not None:
                self.list_panel.select_row(self.playlistManager.selected_row, silent=silent)
            return

    def draw(self):
        super(PlayListPanel, self).draw()

    def generate_game_info_list(self, game_modes):
        return get_game_info_data(SteamGetCurrentLobby(), game_modes)
