from aoslib.scenes import Scene, ElementScene, MenuScene
from aoslib.network import QueryClient
from shared.constants import A1054, A2362, A2361
from aoslib.web import get_servers
from aoslib.text import list_font, title_font, network_font, brushed_font, map_info_font, EDO_FONT, Label, split_text_to_fit_screen, START_FONT, draw_text_within_boundaries
from aoslib.gui import TextButton, Checkbox, ListGrid, TextCheckbox, SquareButton, ImageButton, create_large_navbar
from aoslib.images import global_images
from pyglet.app import event_loop
from pyglet import gl
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.tools import make_server_identifier
from shared.steam import SteamGetInternetServerList, SteamGetInternetOfficialServerList, SteamGetInternetUserServerList, SteamGetLANServerList, SteamGetFavouriteServerList, SteamGetHistoryServerList, SteamGetFriendsServerList, SteamAddFavouriteServer, SteamRemoveFavouriteServer, SteamClearServerRequest, SteamActivateGameOverlayToStore, SteamIsDemoRunning
from shared.constants import A1054, A1056, A2448, A8, A4, A5, A6, A7, A2387, A0
from aoslib.common import collides
from shared.constants_gamemode import A2449
from shared.constants_shop import DLC_APPID_LIST
from aoslib import strings
from serverInfo import ServerInfo
import playlists

class ServerMenu(MenuScene):
    title = strings.PLAY_ONLINE
    server_list = None
    list_display = None
    network_type = strings.INTERNET_ALL
    filter_full_servers = filter_empty_servers = True
    status_text = ''
    show_map_preview = True
    show_buy_options = False

    def initialize(self):
        self.tabs = []
        self.region_ids = []
        self.draw_tab = True
        self.current_tab_index = None
        index = 0
        default_region = self.config.server_region
        for region, region_name in A8.iteritems():
            if region == default_region:
                self.current_tab_index = index
            tab_label = Label(strings.get_by_id(region_name.upper()), font_name=EDO_FONT, font_size=14, anchor_x='center')
            self.tabs.append(tab_label)
            self.region_ids.append(region)
            index += 1

        if self.current_tab_index is None:
            self.current_tab_index = 0
        name_width = 103
        player_width = 68
        map_width = 100
        mode_width = 132
        ping_width = 45
        columns = [(strings.NAME, name_width),
         (strings.PLAYERS, player_width),
         (strings.MAP, map_width),
         (strings.MODE, mode_width),
         (strings.PING, ping_width)]
        self.inital_selected_column_index = 4
        self.list_display = ListGrid(65, 436, 435, 300, columns, self.inital_selected_column_index)
        self.list_display.add_handler(self.server_selection_changed)
        self.net_options = [strings.INTERNET_ALL,
         strings.INTERNET_OFFICIAL,
         strings.INTERNET_USER,
         strings.FAVORITES,
         strings.HISTORY,
         strings.LOCAL]
        self.net_index = 0
        self.draw_tab = strings.INTERNET_OFFICIAL == self.net_options[self.net_index]
        self.refresh_required = False
        self.fav_count = 0
        net_button_size = 20
        net_button_y = 494
        self.net_left = SquareButton(global_images.left_arrow, 154, net_button_y, net_button_size)
        self.net_left.add_handler(self.on_net_left)
        self.net_right = SquareButton(global_images.right_arrow, 287, net_button_y, net_button_size)
        self.net_right.add_handler(self.on_net_right)
        filter_y = 480
        filter_width = 500
        self.full_filter = TextCheckbox(strings.FULL_SERVERS, self.filter_full_servers, 726, filter_y, filter_width)
        self.full_filter.add_handler(self.on_full_filter)
        self.empty_filter = TextCheckbox(strings.EMPTY_SERVERS, self.filter_empty_servers, 549, filter_y, filter_width)
        self.empty_filter.add_handler(self.on_empty_filter)
        pad = 7
        button_y = 130
        button_height = 30
        self.refresh_button = TextButton(strings.REFRESH, 288, button_y, 120, button_height)
        self.refresh_button.add_handler(self.refresh_pressed)
        self.favorite_button = TextButton(strings.FAVORITE, 410 + pad, button_y, 120 - pad, button_height, image=global_images.favorite_star_button)
        self.favorite_button.add_handler(self.favorite_pressed)
        self.navigation_bar = create_large_navbar()
        self.navigation_bar.add_handler(self.back_pressed)
        self.connect_button = TextButton(strings.CONNECT, 543, 153, 190, 54, size=26)
        self.connect_button.add_handler(self.connect_pressed)
        self.elements = [self.full_filter,
         self.empty_filter,
         self.net_left,
         self.net_right,
         self.list_display,
         self.refresh_button,
         self.favorite_button,
         self.navigation_bar]
        self.demo_buy_button = TextButton(strings.BUY_NOW, 543, 153, 190, 54, size=25)
        self.demo_buy_button.add_handler(self.buy_pressed)
        self.demo_buy_button.tint = (0.2, 1.0, 0.2)
        self.demo_buy_button.text_colour = (255, 255, 255, 255)
        self.dlc_buy_button = TextButton(strings.BUY_NOW, 562, 160, 160, 40, size=25)
        self.dlc_buy_button.add_handler(self.buy_pressed)
        self.dlc_buy_button.tint = (0.2, 1.0, 0.2)
        self.dlc_buy_button.text_colour = (255, 255, 255, 255)
        if strings.language == 'english':
            dlc_font_size = 12
        else:
            dlc_font_size = 11
        self.dlc_description = Label('', x=640, y=280, width=180, height=100, anchor_x='center', anchor_y='top', font_name=START_FONT, font_size=dlc_font_size, color=(255, 255, 255, 255))
        dlc_description_text = strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_1) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_2) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_3) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_4) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_5) + '\n'
        self.dlc_description.text = split_text_to_fit_screen(self.dlc_description.font, dlc_description_text, self.dlc_description.width, 0)
        self.query_client = QueryClient(self.on_server_response)
        self.mode_description = Label('', x=547, y=241, width=184, height=60, anchor_x='left', anchor_y='top', font_name=START_FONT, font_size=11, color=A1054)

    def on_start(self, *arg, **kw):
        self.refresh()
        if not self.media.is_playing_music('mainmenu'):
            self.media.play_music('mainmenu', self.config.music_volume)

    def on_stop(self):
        SteamClearServerRequest()
        return super(ServerMenu, self).on_stop()

    def close(self):
        self.media.stop_music(True)

    def got_servers(self, servers):
        if self.network_type != strings.INTERNET_ALL and self.network_type != strings.INTERNET_OFFICIAL and self.network_type != strings.INTERNET_USER:
            return
        self.status_text = strings.RECEIVED_N_SERVERS.format(len(servers))
        self.query_client.query(servers)

    def set_tab(self, index):
        self.current_tab_index = index
        self.config.server_region = self.region_ids[index]
        self.config.save()
        self.refresh()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.draw_tab:
            x1 = 59
            x2 = x1 + global_images.server_tab_name_frame.width
            y1 = 445
            y2 = y1 + 30
            for index, tab in enumerate(self.tabs):
                if collides(x1, y1, x2, y2, x, y, x, y):
                    self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
                    self.set_tab(index)
                    return
                x2 += global_images.server_tab_name_frame.width + 5

        ElementScene.on_mouse_press(self, x, y, button, modifiers)

    def on_net_left(self):
        self.on_net_filter(-1)

    def on_net_right(self):
        self.on_net_filter(1)

    def on_net_filter(self, direction):
        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.net_index = (self.net_index + direction) % len(self.net_options)
        self.network_type = self.net_options[self.net_index]
        self.draw_tab = strings.INTERNET_OFFICIAL == self.net_options[self.net_index]
        self.refresh()

    def on_full_filter(self):
        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.filter_full_servers = self.full_filter.value
        self.update_filters()

    def on_empty_filter(self):
        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.filter_empty_servers = self.empty_filter.value
        self.update_filters()

    def update_filters(self):
        hidden_lines = set()
        for line in self.list_display.lines:
            if self.check_filter(line.server):
                hidden_lines.add(line)

        self.list_display.hidden_lines = hidden_lines
        self.list_display.update_displayed_lines()

    def check_filter(self, server):
        if not self.filter_full_servers and server.count == server.max:
            return True
        if not self.filter_empty_servers and server.count == 0:
            return True
        return False

    def send_favorite_query(self, ip, port):
        self.query_client.send_query(ip, port, True)

    def on_double_click(self, *arg, **kw):
        if not self.list_display.is_over():
            return
        self.connect()

    def connect_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.connect()

    def connect(self):
        line = self.list_display.get_selected()
        valid_to_connect, owns_content = self.valid_to_connect_to_selection(line)
        if not valid_to_connect or not owns_content:
            return
        from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
        if line.server.__class__.__name__ == 'ServerInfo':
            expected_mode = line.server.mode_id
            expected_classic = line.server.classic
            expected_skin = line.server.texture_skin
        else:
            expected_mode = None
            expected_classic = None
            expected_skin = None
        self.parent.set_menu(LoadingMenu, identifier=line.server.identifier, from_server_menu=True, expected_map=line.server.map, expected_mode=expected_mode, expected_classic=expected_classic, expected_skin=expected_skin, previous_menu=type(self))

    def favorite_pressed(self):
        line = self.list_display.get_selected()
        if line is None:
            return
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        server = line.server
        key = (server.ip, server.port)
        favourite_servers = self.manager.favourite_servers
        if line.image:
            SteamRemoveFavouriteServer(server.ipn, server.port, server.queryPort, False)
            favourite_servers.discard(key)
        else:
            SteamAddFavouriteServer(server.ipn, server.port, server.queryPort, False)
            favourite_servers.add(key)
        self.update_favorite(line)

    def update_favorite(self, line):
        server = line.server
        key = (server.ip, server.port)
        if key in self.manager.favourite_servers:
            line.image = global_images.favorite_star
        else:
            line.image = None

    def back_pressed(self, is_back):
        if is_back:
            self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
            from joinMatchMenu import JoinMatchMenu
            self.parent.set_menu(JoinMatchMenu, back=True)

    def buy_pressed(self):
        self.media.play('menu_buyA', zone=HUD_AUDIO_ZONE)
        if not SteamIsDemoRunning():
            SteamActivateGameOverlayToStore(DLC_APPID_LIST['mafia'])
        else:
            SteamActivateGameOverlayToStore(A0)

    def refresh_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.refresh()

    #def refresh(self):
    #    if self.manager.setting_favourites:
    #        self.fav_count += 1
    #        if self.fav_count > 200:
    #            self.fav_count = 0
    #            self.manager.setting_favourites = False
    #        self.refresh_required = True
    #        return
    #    self.query_client.stop()
    #    network_type = self.network_type
    #    region = A8[self.region_ids[self.current_tab_index]]
    #    if self.manager.favourite_servers == None:
    #        self.manager.favourite_servers = set()
    #        self.manager.setting_favourites = True
    #        if SteamGetFavouriteServerList(self.got_server_callback, self.finished_getting_servers_callback):
    #            self.status_text = strings.GETTING_SERVER_LIST
    #        else:
    #            self.status_text = ''
    #            self.manager.setting_favourites = False
    #        return
    #    if network_type == strings.INTERNET_ALL:
    #        if SteamGetInternetServerList(A2387, self.got_server_callback, self.finished_getting_servers_callback, region):
    #            self.status_text = strings.GETTING_SERVER_LIST
    #        else:
    #            self.status_text = ''
    #    elif network_type == strings.INTERNET_OFFICIAL:
    #        print 'internet official'
    #        if SteamGetInternetOfficialServerList(A2387, self.got_server_callback, self.finished_getting_servers_callback, region):
    #            self.status_text = strings.GETTING_SERVER_LIST
    #        else:
    #            self.status_text = ''
    #    if network_type == strings.INTERNET_USER:
    #        if SteamGetInternetUserServerList(A2387, self.got_server_callback, self.finished_getting_servers_callback, region):
    #            self.status_text = strings.GETTING_SERVER_LIST
    #        else:
    #            self.status_text = ''
    #    elif network_type == strings.LOCAL:
    #        if SteamGetLANServerList(self.got_server_callback, self.finished_getting_servers_callback):
    #            self.status_text = strings.QUERYING_LOCAL_SERVERS
    #    elif network_type == strings.FAVORITES:
    #        if SteamGetFavouriteServerList(self.got_server_callback, self.finished_getting_servers_callback):
    #            self.status_text = strings.GETTING_SERVER_LIST
    #        else:
    #            self.status_text = ''
    #    elif network_type == strings.HISTORY:
    #        if SteamGetHistoryServerList(self.got_server_callback, self.finished_getting_servers_callback):
    #            self.status_text = strings.GETTING_SERVER_LIST
    #        else:
    #            self.status_text = ''
    #    elif network_type == strings.FRIENDS:
    #        if SteamGetFriendsServerList(self.got_server_callback, self.finished_getting_servers_callback):
    #            self.status_text = strings.GETTING_SERVER_LIST
    #        else:
    #            self.status_text = ''
    #    self.favorite_button.enabled = False
    #    self.list_display.clear()
    def refresh(self):
        if self.manager.setting_favourites:
            self.fav_count += 1
            if self.fav_count > 200:
                self.fav_count = 0
                self.manager.setting_favourites = False
            self.refresh_required = True
            return

        self.query_client.stop()
        self.status_text = strings.GETTING_SERVER_LIST
        self.favorite_button.enabled = False
        self.list_display.clear()

        from aoslib.web import TYPE_ALL, TYPE_COMMUNITY, TYPE_FAVORITES, TYPE_OFFICIAL, get_servers
        region = 'all'
        if self.draw_tab and self.current_tab_index is not None:
            region = A8[self.region_ids[self.current_tab_index]]

        if self.network_type == strings.INTERNET_OFFICIAL:
            server_type = TYPE_OFFICIAL
        elif self.network_type == strings.INTERNET_USER:
            server_type = TYPE_COMMUNITY
        elif self.network_type == strings.FAVORITES:
            server_type = TYPE_FAVORITES
        else:
            server_type = TYPE_ALL

        d = get_servers(region=region, server_type=server_type)
        d.addCallback(self.got_servers)
        d.addErrback(self.on_server_error)

    def got_servers(self, servers):
        self.status_text = strings.RECEIVED_N_SERVERS.format(len(servers))
        for server in servers:
            ping = getattr(server, 'ping', 50)
            try:
                ping = int(round(float(ping)))
            except (TypeError, ValueError):
                ping = 50

            player_count = getattr(server, 'players', getattr(server, 'count', 0))
            max_players = getattr(server, 'max_players', getattr(server, 'max', 0))
            players = '%s/%s' % (player_count, max_players)
            players_sort_key = player_count * 256 + max_players

            line = self.list_display.add_line((
                server.name,
                (players, players_sort_key),
                server.map,
                server.game_mode,
                (str(ping), ping)
            ), server=server)

            if self.check_filter(server):
                self.list_display.hide([line])
            self.update_favorite(line)

    def on_server_error(self, error):
        self.status_text = strings.SERVER_LIST_ERROR
        print "Error getting servers:", error

    def got_server_callback(self, name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played):
        server = ServerInfo(name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played)
        print 'got server ' + name
        if not server.monitor and server.is_matching_version:
            if self.manager.setting_favourites:
                key = (server.ip, server.port)
                self.manager.favourite_servers.add(key)
            else:
                self.on_server_response(server, ping / 1000.0)

    def finished_getting_servers_callback(self):
        print 'finished getting servers'
        self.status_text = ''
        self.status_text = strings.RECEIVED_N_SERVERS.format(len(self.list_display.lines))

    def valid_to_connect_to_selection(self, selected = None, reason = None):
        if not selected:
            selected = self.list_display.get_selected()
        if selected:
            if SteamIsDemoRunning():
                try:
                    playlist_id = int(selected.server.playlist_id)
                    playlist = playlists.play_lists_by_id[playlist_id]
                    map_name = selected.server.map
                    map_info = playlists.mapinfo.map_info[map_name]
                    if playlist.demo == True and map_info['demo'] == True:
                        return (True, True)
                    return (True, False)
                except:
                    return (False, False)

            else:
                texture_skin = selected.server.texture_skin
                if texture_skin and texture_skin in DLC_APPID_LIST and not self.manager.dlc_manager.is_installed_dlc(texture_skin):
                    return (True, False)
                else:
                    return (True, True)
        return (False, True)

    def server_selection_changed(self):
        valid_to_connect, owns_content = self.valid_to_connect_to_selection()
        self.favorite_button.enabled = valid_to_connect != None
        if valid_to_connect and owns_content:
            self.show_map_preview = True
            self.show_buy_options = False
            if self.connect_button not in self.elements:
                self.elements.append(self.connect_button)
            if self.dlc_buy_button in self.elements:
                self.elements.remove(self.dlc_buy_button)
            if self.demo_buy_button in self.elements:
                self.elements.remove(self.demo_buy_button)
        else:
            self.show_map_preview = False
            if self.connect_button in self.elements:
                self.elements.remove(self.connect_button)
            self.show_buy_options = not owns_content
            if self.show_buy_options:
                if SteamIsDemoRunning():
                    self.show_map_preview = True
                    if self.demo_buy_button not in self.elements:
                        self.elements.append(self.demo_buy_button)
                    if self.dlc_buy_button in self.elements:
                        self.elements.remove(self.dlc_buy_button)
                else:
                    if self.dlc_buy_button not in self.elements:
                        self.elements.append(self.dlc_buy_button)
                    if self.demo_buy_button in self.elements:
                        self.elements.remove(self.demo_buy_button)
            else:
                if self.dlc_buy_button in self.elements:
                    self.elements.remove(self.dlc_buy_button)
                if self.demo_buy_button in self.elements:
                    self.elements.remove(self.demo_buy_button)

    def on_server_response(self, server, ping):
        for line in self.list_display.lines:
            if line.server.ip == server.ip and line.server.port == server.port:
                return

        ping = int(ping * 1000)
        players = '%s/%s' % (server.count, server.max)
        players_sort_key = server.count * 256 + server.max
        line = self.list_display.add_line((server.name,
         (players, players_sort_key),
         server.map,
         server.game_mode,
         (str(ping), ping)), server=server)
        if self.check_filter(server):
            self.list_display.hide([line])
        self.update_favorite(line)
        if self.list_display.selected_column == None:
            self.list_display.select_column(self.inital_selected_column_index)

    def update(self, dt):
        if self.refresh_required:
            self.refresh_required = False
            self.refresh()
        self.query_client.update(dt)

    def draw(self):
        mid_x, mid_y = 800 / 2, 600 / 2
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        global_images.large_frame.blit(mid_x, mid_y)
        title_font.draw(self.title.upper(), mid_x, 540, A1054, center=True)
        self.navigation_bar.draw()
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        global_images.server_content_frame.blit(mid_x, mid_y)
        lines = split_text_to_fit_screen(list_font, self.status_text, 200, 20).split('\n')
        line_y = 120
        for line in lines:
            list_font.draw(line, 76, line_y, A1054)
            line_y -= 10

        if self.show_buy_options and not SteamIsDemoRunning():
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            self.dlc_description.draw()
        for element in self.elements:
            element.draw()

        network_font.draw(self.network_type.upper(), 220, 488, A1054, center=True)
        brushed_font.draw(strings.NETWORK, 71, 489, A1054)
        list_font.draw('', 541, 218, A1054)
        if self.draw_tab:
            tab_frame_x = 116
            tab_x = tab_frame_x
            tab_y = 460
            for index, tab in enumerate(self.tabs):
                if index == self.current_tab_index:
                    global_images.server_tab_name_frame.blit(tab_frame_x, tab_y - 1)
                    tab.color = A1056
                else:
                    tab.color = A1054
                tab.x = tab_frame_x
                tab.y = tab_y - 5
                tab.draw()
                tab_frame_x += global_images.server_tab_name_frame.width + 5

        if self.show_map_preview:
            line = self.list_display.get_selected()
            if line:
                map_info_font.draw(line.server.map, 638, 451, A1054, center=True)
                try:
                    image = global_images.map_previews[line.server.map][1]
                    if image is None:
                        raise KeyError()
                    map_preview = image.blit(542, 246, width=300 * global_images.global_scale, height=300 * global_images.global_scale)
                    description = strings.get_by_id(A2449[line.server.mode_tla])
                    if description is not None:
                        draw_text_within_boundaries(description, 547, 225, self.mode_description.width, 70, self.mode_description.font, 3, A1054)
                except KeyError as IndexError:
                    global_images.map_placeholder.blit(542, 246, width=300 * global_images.global_scale, height=300 * global_images.global_scale)
