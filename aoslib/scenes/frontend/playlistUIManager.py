from aoslib.scenes.main.playlistItem import PlaylistItem
from aoslib.scenes.main.matchSettings import get_game_mode_names, get_default_match_length_for_playlist_in_minutes
from aoslib import strings
from shared.constants_gamemode import A2450
from shared.constants_matchmaking import A2667, A2688, A2665
from shared.steam import SteamGetLobbyData, SteamSetLobbyData, SteamGetCurrentLobby, SteamAmITheLobbyOwner
from aoslib.ugc_data import get_available_game_modes, get_all_available_custom_map_names
import playlists

class PlayListUIManager(object):

    def __init__(self, list_panel, allow_multiple_modes_lists=True, multiple_maps=True, allow_selecting_unowned=False, ugc_mode=False):
        self.playlist_id = 0
        self.selected_row = None
        self.list_panel = list_panel
        self.allow_multiple_modes_lists = allow_multiple_modes_lists
        self.multiple_maps = multiple_maps
        self.allow_selecting_unowned = allow_selecting_unowned
        self.ugc_mode = ugc_mode
        self.populate_playlist()
        return

    def save_selected_row(self):
        if self.list_panel is not None:
            self.selected_row = self.list_panel.get_selected_item()
        return

    def generate_game_info_list(self, game_modes):
        return get_game_mode_names(game_modes)

    def get_selected_playlist_default_rules_as_string(self):
        rules = []
        for play_list in playlists.play_lists:
            if play_list.id != self.playlist_id:
                continue
            for rule_id, value in play_list.config.iteritems():
                text = strings.get_by_id(rule_id) + ': ' + value
                rules.append(text)

            break

        return rules

    def populate_playlist(self):
        if self.list_panel is None:
            return
        else:
            playlist = {}
            play_list_info = playlists.play_lists
            for play_list in play_list_info:
                if self.allow_multiple_modes_lists == False and len(play_list.modes) > 1 or play_list.tutorial:
                    continue
                game_info_list = self.generate_game_info_list(play_list.modes)
                if self.multiple_maps:
                    maps = play_list.map_names
                else:
                    maps = []
                    for map_name in play_list.map_names:
                        maps.append(map_name)
                        break

                game_modes = []
                for mode in play_list.modes:
                    if mode == 'ctf' and play_list.classic:
                        game_modes.append('cctf')
                    else:
                        game_modes.append(mode)

                playlist[play_list.id] = {'name': (play_list.name), 'game_info': game_info_list, 'map': maps, 'server_type': (strings.PUBLIC), 'modes': game_modes}

            random_item = None
            list = []
            for id, data in playlist.iteritems():
                if not self.ugc_mode and data['modes'][0] == 'ugc':
                    continue
                item = PlaylistItem(id, data['name'], data['game_info'], data['map'], data['server_type'], data['modes'], self.list_panel.manager.dlc_manager, self.allow_selecting_unowned)
                item.center_text = False
                if data['name'] == strings.RANDOM:
                    random_item = item
                else:
                    list.append(item)

            list = sorted(list, key=(lambda item: item.name))
            if random_item is not None:
                list.insert(0, random_item)
            for row in [row for row in self.list_panel.rows if hasattr(row, 'close')]:
                row.close()

            self.list_panel.rows = list
            self.list_panel.on_scroll(0, silent=True)
            return

    def on_row_selected(self, index, row):
        if SteamGetCurrentLobby() != 0 and not SteamAmITheLobbyOwner():
            return
        else:
            if row is None:
                return
            self.update_lobby_data(row.id, row.server_type, row.map_rotation, row.modes)
            self.playlist_id = row.id
            return

    def update_lobby_data(self, playlist_id, server_type, map_rotation, map_modes):
        lobby_id = SteamGetCurrentLobby()
        for category in A2667.itervalues():
            for rule_id in category:
                lobby_value = SteamGetLobbyData(lobby_id, rule_id)
                old_default_value = playlists.get_default_rule_value_for_playlist(rule_id, self.playlist_id)
                if lobby_value == '' or lobby_value == old_default_value:
                    new_default_value = playlists.get_default_rule_value_for_playlist(rule_id, playlist_id)
                    if new_default_value == A2688[rule_id]['default']:
                        SteamSetLobbyData(rule_id, '')
                    else:
                        SteamSetLobbyData(rule_id, new_default_value)

        previous_default_match_length = get_default_match_length_for_playlist_in_minutes(self.playlist_id)
        new_default_match_length = get_default_match_length_for_playlist_in_minutes(playlist_id)
        current_match_length = SteamGetLobbyData(lobby_id, 'MATCH_LENGTH')
        if current_match_length == str(previous_default_match_length) or current_match_length == '':
            SteamSetLobbyData('MATCH_LENGTH', str(new_default_match_length))

    def is_map_valid_for_playlist(self, map_name, custom_ugc_map='False', current_playlist=None):
        if not current_playlist:
            current_playlist = next((playlist for playlist in playlists.play_lists if playlist.id == self.playlist_id), None)
            if current_playlist is None:
                return False
        if custom_ugc_map != 'False':
            map_names = get_all_available_custom_map_names()
            if map_name in map_names:
                if self.ugc_mode:
                    return True
                else:
                    modes = get_available_game_modes(map_name)
                    if A2450[current_playlist.modes[0]] in modes:
                        return True
                    return False

            else:
                if map_name in current_playlist.map_names:
                    return True
                else:
                    return False

        return map_name in current_playlist.map_names

    def draw(self):
        super(PlayListMenuBase, self).draw()
