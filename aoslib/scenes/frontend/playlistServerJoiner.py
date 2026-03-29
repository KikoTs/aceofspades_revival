import urllib
from twisted.web.client import getPage
from twisted.internet import reactor
from shared.steam import SteamGetInternetServerList, SteamGetSessionTicket, SteamGetAllLobbyData
import json
from serverInfo import ServerInfo
from shared.constants import SERVER_REGIONS, REGION_US_WEST, REGION_US_EAST, REGION_EUROPE, REGION_AUSTRALIA, SERVERMODE_PUBLIC

class PlaylistServerJoiner:
    client = None
    playlist = 0
    searching = False
    join_when_ready = False
    is_ready = False
    servers = []

    def __init__(self, client, playlist_id):
        self.client = client
        self.playlist_id = playlist_id

    def begin_search(self):
        self.join_when_ready = False
        self.is_ready = False
        self.servers = []
        if SteamGetInternetServerList(SERVERMODE_PUBLIC, self.got_server_callback, self.finished_getting_servers_callback):
            self.searching = True
            return True
        else:
            self.searching = False
            return False

    def join(self):
        self.join_when_ready = True
        if self.is_ready:
            self.request_server_async()

    def cancel(self):
        self.searching = False

    def got_server_callback(self, name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played):
        server = ServerInfo(name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played)
        if not server.is_matching_version:
            return
        if self.playlist_id != 0 and int(self.playlist_id) != int(server.playlist_id):
            return
        self.servers.append(server)

    def query_client_response(self, server, ping):
        self.servers.append(server)

    def finished_getting_servers_callback(self):
        self.is_ready = True
        if self.join_when_ready:
            self.request_server_async()

    def request_server_async(self):
        server = self.choose_existing_server()
        if server:
            self.client.found_server(server.ip, server.port)

    def choose_existing_server(self):
        if len(self.servers) == 0:
            return self.client.cancel_game_with_broadcast_error('LOBBY_ERROR_NO_SERVERS_FOUND')
        required_slots = self.client.get_num_player_slots_required()
        low_ping_servers = []
        populated_servers = []
        empty_servers = []
        ping_sorted = sorted(self.servers, key=(lambda server: server.ping))
        low_ping = ping_sorted[0].ping * 2.0
        for server in self.servers:
            if server.count > 0 and server.count < server.max - required_slots:
                if server.ping < low_ping:
                    low_ping_servers.append(server)
                else:
                    populated_servers.append(server)
            elif server.count == 0 and server.max >= required_slots:
                empty_servers.append(server)

        import random
        noof_low_ping_servers = len(low_ping_servers)
        noof_populated_servers = len(populated_servers)
        noof_empty_servers = len(empty_servers)
        if noof_low_ping_servers == 0 and noof_populated_servers == 0 and noof_empty_servers == 0:
            return self.client.cancel_game_with_broadcast_error('LOBBY_ERROR_NO_SERVERS_FOUND')
        if noof_low_ping_servers > 0:
            index = random.randint(0, noof_low_ping_servers - 1)
            server = low_ping_servers[index]
        elif noof_populated_servers > 0:
            index = random.randint(0, noof_populated_servers - 1)
            server = populated_servers[index]
        elif noof_empty_servers == 0:
            self.client.cancel_game_with_broadcast_error('LOBBY_ERROR_ALL_SERVERS_ARE_FULL')
            return
        index = random.randint(0, noof_empty_servers - 1)
        server = empty_servers[index]
        self.server_responses = []
        return server
