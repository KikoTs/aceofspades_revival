from aoslib.tools import make_server_identifier
from aoslib import strings
from shared.constants_gamemode import A2441, A2450, A2448
from shared.constants import CLASSIC, NOT_CLASSIC
from shared.steam import game_version

class ServerInfo(object):

    def __init__(self, name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played):
        self.count = num_players
        self.max = max_players
        self.name = name
        self.port = 32887
        self.ping = ping / 1000.0
        self.map = map
        self.mode_tla = mode
        self.time_last_played = time_last_played
        try:
            self.mode_id = A2450[self.mode_tla]
        except KeyError:
            self.mode_tla = 'tdm'
            self.mode_id = A2441

        self.identifier = make_server_identifier(ip, 32887)
        self.texture_skin = None
        for tag in tags:
            if tag[:5] == 'skin=':
                self.texture_skin = tag[5:]
                break

        self.region = ''
        for tag in tags:
            if tag[:7] == 'region=':
                self.region = tag[7:]
                break

        if 'classic' in tags:
            mode = 'c' + mode
        try:
            game_mode_title = A2448[mode]
        except:
            game_mode_title = 'TDM_TITLE'

        self.game_mode = strings.get_by_id(game_mode_title)
        self.identifier = make_server_identifier(ip, 32887)
        splitted = self.identifier.split(':')
        self.ip = splitted[0]
        self.ipn = ip
        self.port = 32887
        self.queryPort = queryPort
        self.tags = tags
        self.beta = True if 'beta' in tags else False
        self.monitor = True if 'monitor' in tags else False
        self.classic = CLASSIC if 'classic' in tags else NOT_CLASSIC
        client_version = 'v%d' % game_version()
        self.is_matching_version = True
        if tags[1].startswith('playlist='):
            id, num = tags[1].split('=')
            self.playlist_id = num
        else:
            self.playlist_id = 0
        return
