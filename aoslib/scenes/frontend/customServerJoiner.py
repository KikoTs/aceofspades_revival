import urllib
from twisted.web.client import getPage
from twisted.internet import reactor
from shared.steam import SteamGetInternetServerList, SteamGetSessionTicket, SteamGetAllLobbyData, SteamClearServerRequest
import json
from serverInfo import ServerInfo
from shared.constants import SERVER_REGIONS, REGION_US_WEST, REGION_US_EAST, REGION_EUROPE, REGION_AUSTRALIA
from shared.constants import MONITOR_RETURN_SUCCESS, MONITOR_RETURN_INVALID_PARAMETER, MONITOR_RETURN_REQUEST_TOO_FAST, MONITOR_RETURN_MONITOR_FULL, MONITOR_RETURN_STEAM_AUTH_ERROR
from shared.constants import SERVERMODE_MONITOR
from aoslib import strings
SERVER_MON_URL = 'http://{0}:{1}/spawn'
SERVER_MON_CONNECTION_TIMEOUT = 10.0

class CustomServerJoiner:
    client = None
    searching = False
    join_when_ready = False
    is_ready = False
    local_monitor = False
    request_headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    def __init__(self, client, on_target_monitor_changed):
        self.client = client
        default_monitor = self.client.manager.default_server
        self.on_target_monitor_changed = on_target_monitor_changed
        if self.local_monitor or default_monitor is None:
            self._target_monitor = ('127.0.0.1', 8076, 0)
        else:
            self._target_monitor = (
             default_monitor.ip, default_monitor.port, default_monitor.queryPort)
        return

    def begin_search(self):
        region = self.client.manager.default_region
        self.join_when_ready = False
        self.is_ready = self.local_monitor
        self.server_spawners = []
        if SteamGetInternetServerList(SERVERMODE_MONITOR, self.got_server_callback, self.finished_getting_servers_callback, region):
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
        SteamClearServerRequest()

    def got_server_callback(self, name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played):
        server = ServerInfo(name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played)
        if server.is_matching_version:
            self.server_spawners.append(server)
        else:
            print 'Incompatible spawner found:', ip, port, tags

    def finished_getting_servers_callback(self):
        self.is_ready = True
        if self.join_when_ready:
            self.request_server_async()

    def request_server_async(self):
        server = self.choose_server_spawner()
        if self.local_monitor:
            self.server_spawners = []
        if server in self.server_spawners:
            self.server_spawners.remove(server)
        if server or self.local_monitor:
            if not self.local_monitor:
                self.set_target_monitor(server.ip, server.port, server.queryPort)
            try:
                session_ticket = SteamGetSessionTicket()
                config = self.client.build_server_config()
                print(config)
                if config != {}:
                    fields = {'config': (json.dumps(config)), 'ticket': (session_ticket[0])}
                    data = urllib.urlencode(fields)
                    self.request = getPage(SERVER_MON_URL.format(self._target_monitor[0], self._target_monitor[1]), method='POST', postdata=data, headers=self.request_headers, timeout=SERVER_MON_CONNECTION_TIMEOUT)
                    self.request.addCallbacks(self.__request_server_callback, self.__request_server_error_callback)
                    self.join_when_ready = False
            except:
                import traceback
                print traceback.format_exc()
                self.handle_error((lambda : self.client.cancel_game_with_local_error('LOBBY_ERROR_SERVER_CONNECTION_FAILED')))

    def handle_error(self, cancel_function):
        if self.server_spawners:
            self.join_when_ready = self.searching
            self.request_server_async()
        else:
            cancel_function()

    def choose_server_spawner(self):
        if self.local_monitor:
            return None
        else:
            if len(self.server_spawners) == 0:
                self.handle_error((lambda : self.client.cancel_game_with_broadcast_error('LOBBY_ERROR_NO_SERVERS_FOUND')))
                return None
            space_allowance_factor = 0.9
            servers_with_space = filter((lambda server: server.count < server.max * space_allowance_factor), self.server_spawners)
            if len(servers_with_space) == 0:
                servers_with_space = filter((lambda server: server.count < server.max), self.server_spawners)
                if len(servers_with_space) == 0:
                    self.handle_error((lambda : self.client.cancel_game_with_broadcast_error('LOBBY_ERROR_ALL_SERVERS_ARE_FULL')))
                    return None
            ping_sorted = sorted(servers_with_space, key=(lambda server: server.ping))
            ping_threshold = 50 / 1000.0
            max_ping = ping_sorted[0].ping + ping_threshold
            ping_filtered = filter((lambda server: server.ping <= max_ping), ping_sorted)
            capacity_sorted = sorted(ping_filtered, key=(lambda server: server.count / float(server.max)))
            return capacity_sorted[0]

    def set_target_monitor(self, ip, port, queryPort):
        new_monitor = (ip, port, queryPort)
        if not self.local_monitor:
            self._target_monitor = new_monitor
        if self.on_target_monitor_changed:
            self.on_target_monitor_changed(new_monitor)

    def __request_server_callback(self, result):
        if result and self.searching:
            response = None
            try:
                response = json.loads(result)
            except:
                import traceback
                print traceback.format_exc()
                try:
                    errortext = strings.get_by_id_or_except('LOBBY_ERROR_SERVER_ERROR_' + str(result))
                    self.handle_error((lambda : self.client.cancel_game_with_local_error(errortext)))
                except:
                    self.handle_error((lambda : self.client.cancel_game_with_local_error(u'{0} - {1}', (strings.get_by_id('LOBBY_ERROR_SERVER_ERROR'), result))))

            if response['result'] == MONITOR_RETURN_SUCCESS:
                self.client.found_server(self._target_monitor[0], int(response['port']))
            else:
                errorcode = response['result']
            try:
                errortext = strings.get_by_id_or_except('LOBBY_ERROR_SERVER_ERROR_' + str(errorcode))
                self.handle_error((lambda : self.client.cancel_game_with_local_error(errortext)))
            except:
                self.handle_error((lambda : self.client.cancel_game_with_local_error(u'{0} - {1}', (strings.get_by_id('LOBBY_ERROR_SERVER_ERROR'), errorcode))))

        return

    def __request_server_error_callback(self, result):
        if self.searching:
            error_num = -1
            try:
                if hasattr(result.value, 'osError'):
                    error_num = result.value.osError
                elif hasattr(result.value, 'status'):
                    error_num = result.value.status
            except:
                pass

            if error_num == 10051 or error_num == 10065:
                errortext = strings.NO_STEAM_CONNECTION
                self.handle_error((lambda : self.client.cancel_game_with_local_error(errortext)))
            else:
                try:
                    errortext = strings.get_by_id_or_except('LOBBY_ERROR_SERVER_REQUEST_FAILED_' + str(error_num))
                    self.handle_error((lambda : self.client.cancel_game_with_local_error(errortext)))
                except:
                    self.handle_error((lambda : self.client.cancel_game_with_local_error(strings.get_by_id('LOBBY_ERROR_SERVER_REQUEST_FAILED'), (error_num,))))
