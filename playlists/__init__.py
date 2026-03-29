import os, sys, glob, imp
from shared.common import *
from shared.constants_matchmaking import A2688
from shared.steam import SteamGetLobbyData, SteamGetCurrentLobby
try:
    from aoslib import strings
    no_strings = False
except:
    no_strings = True

import mapinfo, ast
next_id = 1

class PlayList:

    def __init__(self, file):
        global next_id
        path, filename = os.path.split(file)
        file_contents = open(file, 'r').read()
        file_contents = ('').join(file_contents.splitlines())
        info = ast.literal_eval(file_contents)
        if no_strings:
            self.name = info['name']
        else:
            self.name = strings.get_by_id(info['name'])
        self.id = next_id
        next_id += 1
        self.modes = info['modes']
        self.ugc_modes = info['ugc_modes']
        self.classic = info['classic']
        self.mafia = info['mafia']
        self.players = info['players']
        self.tutorial = info['tutorial']
        self.demo = info['demo']
        self.map_names = info['maps']
        self.maps = []
        self.config = info['config']
        for mode in self.modes:
            for map_name, map_data in mapinfo.map_info.iteritems():
                if len(self.map_names) > 0 and map_name not in self.map_names:
                    continue
                if mode in map_data['invalid_modes']:
                    continue
                if self.classic != map_data['classic']:
                    continue
                if self.mafia != map_data['mafia']:
                    continue
                if not map_data['release']:
                    continue
                self.maps.append(mode + '_' + map_name)

        self.map_names = set()
        for map in self.maps:
            mode, name = map.split('_')
            self.map_names.add(name)


paths = sorted(glob.glob(os.path.join(os.getcwd(), get_relative_path(['../../common', '../common', './common'], 'playlists'), '*.txt')))
play_lists = []
play_lists_by_id = {}
for file in paths:
    playlist = PlayList(file)
    play_lists.append(playlist)
    play_lists_by_id[playlist.id] = playlist

def get_mode_playlist(mode):
    import playlists
    for playlist in playlists.play_lists:
        if len(playlist.modes) == 1 and mode in playlist.modes:
            return playlist

    return


def get_default_rule_value_for_current_lobby(rule_id):
    return get_default_rule_value_for_lobby(rule_id, SteamGetCurrentLobby())


def get_default_rule_value_for_lobby(rule_id, lobby_id):
    playlist_id_as_string = SteamGetLobbyData(lobby_id, 'PlaylistID')
    try:
        playlist_id = int(playlist_id_as_string)
        return get_default_rule_value_for_playlist(rule_id, playlist_id)
    except ValueError:
        return A2688[rule_id]['default']


def get_default_rule_value_for_playlist(rule_id, playlist_id):
    try:
        playlist = play_lists_by_id[playlist_id]
        if rule_id in playlist.config:
            return playlist.config[rule_id]
    except KeyError:
        pass

    return A2688[rule_id]['default']


if 'allmaps' not in sys.argv:
    maps_to_delete = []
    for map_name, map_data in mapinfo.map_info.iteritems():
        if not map_data['release']:
            maps_to_delete.append(map_name)

    for map_name in maps_to_delete:
        mapinfo.map_info.pop(map_name, None)
