from aoslib import strings
from shared.constants_matchmaking import *
from shared.steam import SteamGetLobbyData, SteamSetLobbyData, SteamGetLobbyOwner, SteamGetFriendPersonaName
from shared.constants_gamemode import A2448
from shared.constants_prefabs import A3056
import re
from aoslib.ugc_data import get_noof_existing_titles, get_does_title_exist, get_ugc_map_filenames_with_name
DEFAULT_MATCH_SETTINGS = {'MAX_PLAYERS': '12', 
   'MATCH_LENGTH': '10', 
   'PRIVACY': A2715, 
   'PLAYLIST': [], 'UGC_MODES': [], 'PREFAB_SET': '1', 
   'MAP_ROTATION_FILENAME': []}

def generate_ugc_map_filename_from_lobby(lobby_id):
    name = SteamGetLobbyData(lobby_id, 'MAP_ROTATION_NEW_TITLE')
    return generate_ugc_map_filename(name)


def generate_ugc_map_filename(map_name):
    name = 'Custommap'
    files = get_ugc_map_filenames_with_name(name)
    count = len(files)
    if count > 0:
        start_name = name
        while len(files) != 0:
            count += 1
            name = start_name + '_' + str(count)
            files = get_ugc_map_filenames_with_name(name)

    else:
        name += '_1'
    return name


def generate_ugc_map_title(map_name):
    name = map_name
    exists = get_does_title_exist(name)
    if exists:
        start_name = name
        increment = 0
        while exists != False:
            increment += 1
            name = start_name + '-' + str(increment)
            exists = get_does_title_exist(name)

    return name


def reset_all_game_rules():
    for rule_id in A2688.keys():
        SteamSetLobbyData(rule_id, '')


def get_game_rules_and_values_as_string(lobby_id):
    rules_string = ''
    for rule_id in A2688.keys():
        rule_value = SteamGetLobbyData(lobby_id, rule_id)
        if rule_value != '':
            if rules_string != '':
                rules_string += ','
            rules_string += strings.get_by_id(rule_id)
            if rule_value != 'ON':
                rules_string += ': ' + rule_value

    return rules_string


def get_game_rules_and_values_list(lobby_id):
    rules_text = get_game_rules_and_values_as_string(lobby_id)
    return get_string_as_list(rules_text)


def get_string_as_list(string_text):
    if string_text is None or string_text == '':
        return []
    return string_text.split(',')


def get_list_items_as_string(list):
    items_string = ''
    for item in list:
        if items_string != '':
            items_string += ',' + item
        else:
            items_string += item

    return items_string


def get_game_mode_names(game_modes):
    names = []
    for mode in game_modes:
        if mode in A2448:
            if mode in ('ugc', 'tutorial'):
                continue
            names.append(strings.get_by_id(A2448[mode]))
        else:
            names.append(mode)

    return names


def get_game_info_data(lobby_id, game_modes):
    game_info = get_game_mode_names(game_modes)
    game_info.append(SteamGetLobbyData(lobby_id, 'MAP_ROTATION_NEW_TITLE'))
    for item in ['MAX_PLAYERS', 'MATCH_LENGTH']:
        text = strings.get_by_id(item)
        value = SteamGetLobbyData(lobby_id, item)
        if item == 'MATCH_LENGTH' and value == '0':
            text += ': ' + strings.UNLIMITED
        else:
            text += ': ' + str(value)
        game_info.append(text)

    return game_info


def get_default_playlist():
    import playlists
    for playlist in playlists.play_lists:
        if len(playlist.modes) == 1 and A2666 in playlist.modes:
            return playlist

    return


def get_default_match_length_for_playlist_in_minutes(playlist_id):
    from shared.constants_gamemode import A2503, A2662
    list = get_playlist_with_id(playlist_id)
    if list is not None and len(list.modes) > 0 and list.modes[0] in A2662.keys():
        if list.classic:
            return int(A2662['cctf'] / 60)
        else:
            return int(A2662[list.modes[0]] / 60)

    return int(A2503 / 60)


def get_playlist_with_id(id):
    import playlists
    for playlist in playlists.play_lists:
        if playlist.id == id:
            return playlist

    return


def get_playlist_with_mode(mode):
    import playlists
    return playlists.get_mode_playlist(mode)


def get_default_settings_value(settings_id, default_playlist=None):
    if default_playlist == None:
        default_playlist = get_default_playlist()
    if default_playlist == None:
        return ''
    else:
        if settings_id == 'PLAYLIST':
            return default_playlist.modes
        if settings_id == 'UGC_MODES':
            return default_playlist.ugc_modes
        if settings_id == 'MAP_ROTATION_FILENAME':
            maps = sorted(default_playlist.map_names)
            if len(maps) == 0:
                return ''
            return maps[0]
        if settings_id == 'MATCH_LENGTH':
            return str(get_default_match_length_for_playlist_in_minutes(default_playlist.id))
        if settings_id in DEFAULT_MATCH_SETTINGS:
            return DEFAULT_MATCH_SETTINGS[settings_id]
        return ''


def get_display_name(settings_id, lobby_id=None):
    if settings_id == 'PLAYLIST':
        return __get_playlist_display_name(lobby_id)
    else:
        if settings_id == 'UGC_MODES':
            return __get_ugc_mode_display_name(lobby_id)
        if settings_id == 'MAP_ROTATION_FILENAME':
            return __get_map_rotation_display_name(lobby_id)
        if settings_id == 'GAME_RULES':
            if lobby_id is not None:
                for rule_id in A2688.keys():
                    rule_value = SteamGetLobbyData(lobby_id, rule_id)
                    if rule_value != '':
                        return strings.DEFINED

            return strings.DEFAULT
        if settings_id == 'PREFAB_SET':
            prefab_set_id = SteamGetLobbyData(lobby_id, settings_id)
            if prefab_set_id != '' and int(prefab_set_id) in A3056:
                return strings.get_by_id(A3056[int(prefab_set_id)])
        return strings.get_by_id(settings_id)


def __get_playlist_display_name(lobby_id):
    if lobby_id is not None:
        current_playlist_id_string = SteamGetLobbyData(lobby_id, 'PlaylistID')
        if current_playlist_id_string != '':
            current_playlist = get_playlist_with_id(int(current_playlist_id_string))
            if current_playlist is not None:
                return current_playlist.name
    return strings.DEFAULT


def __get_ugc_mode_display_name(lobby_id):
    if lobby_id is not None:
        current_playlist_id_string = SteamGetLobbyData(lobby_id, 'PlaylistID')
        if current_playlist_id_string != '':
            current_playlist = get_playlist_with_id(int(current_playlist_id_string))
            if current_playlist is not None and len(current_playlist.ugc_modes) > 0:
                mode = current_playlist.ugc_modes[0]
                text = strings.get_by_id(A2448[mode])
                if len(current_playlist.ugc_modes) > 1:
                    for i in xrange(1, len(current_playlist.ugc_modes)):
                        mode = current_playlist.ugc_modes[i]
                        text += strings.get_by_id(A2448[mode]) + ', '

                return text
    return strings.DEFAULT


def __get_map_rotation_display_name(lobby_id):
    if lobby_id == None:
        return ''
    else:
        import playlists
        map_rotation_string = SteamGetLobbyData(lobby_id, 'MAP_ROTATION_FILENAME')
        selected_maps = get_string_as_list(map_rotation_string)
        playlist_id_string = SteamGetLobbyData(lobby_id, 'PlaylistID')
        playlist_maps = None
        same_lists = True
        if playlist_id_string != '':
            id = int(playlist_id_string)
        for item in playlists.play_lists:
            if item.id == id:
                playlist_maps = item.map_names
                break

        if playlist_maps is not None:
            same_lists = sorted(playlist_maps) == sorted(selected_maps)
        else:
            same_lists = False
        if same_lists:
            default_text = strings.DEFAULT
        else:
            default_text = strings.DEFINED
        return default_text
