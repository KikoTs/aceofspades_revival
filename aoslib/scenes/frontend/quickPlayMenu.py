from aoslib.scenes.frontend.listPreviewMenuBase import ListPreviewMenuBase
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.frontend.previewPanelBase import PreviewPanelBase
from aoslib.scenes.frontend.playlistUIManager import PlayListUIManager
from aoslib.scenes.frontend.columnsListPanel import ColumnsListPanel
from aoslib import strings
from aoslib.draw import draw_quad
from aoslib.images import global_images
import playlists
from aoslib.media import HUD_AUDIO_ZONE
from joiningGameMenu import JoiningGameMenu
from shared.constants import A2387, A0
from shared.constants_gamemode import A2450, A2446
from shared.constants_shop import DLC_APPID_LIST
from shared.steam import SteamActivateGameOverlayToStore, SteamIsDemoRunning, SteamGetInternetServerList
from shared.hud_constants import NORMAL_ROW_HEIGHT
from serverInfo import ServerInfo
from pyglet import gl

class QuickPlayMenu(ListPreviewMenuBase):

    def initialize(self):
        super(QuickPlayMenu, self).initialize(strings.PUBLIC_MATCH)
        self.main_button = None
        self.refresh_button = None
        self.buy_now_button = None
        self.list_panel = ColumnsListPanel(self.manager)
        self.preview_panel = PreviewPanelBase(self.manager)
        self.playlistManager = PlayListUIManager(self.list_panel, allow_selecting_unowned=True)
        self.button_height = 50
        self.button_background_x = 0
        self.button_background_y = 0
        self.button_background_scale_x = 1.0
        self.button_background_scale_y = 1.0
        self.refresh_button_background_x = 0
        self.refresh_button_background_y = 0
        self.refresh_button_background_scale_x = 1.0
        self.refresh_button_background_scale_y = 1.0

    def on_start(self, *arg, **kw):
        super(QuickPlayMenu, self).on_start(*arg, **kw)
        self.elements = []
        self.buttons = []
        self.elements.append(self.navigation_bar)
        self.elements.append(self.list_panel)
        self.elements.append(self.preview_panel)
        self.list_panel.initialise_ui(strings.PLAYLISTS, 56, 505, 340, 354, row_height=NORMAL_ROW_HEIGHT - 2, has_header=True)
        self.list_panel.center_header_text = True
        self.list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        self.preview_panel.initialise_ui(None, 401, 505, 340, 354, has_header=True)
        self.create_main_button()
        self.create_refresh_button()
        self.create_buy_button()
        self.list_panel.manager.dlc_manager.append_dlc_installed_callback(self.on_dlc_installed)
        self.list_panel.set_list_panel_columns((strings.MODE, strings.PING, strings.PLAYERS), (185, 60, 70))
        self.list_panel.update_position(56, 505, 340, 354)
        button_background_height = self.button_height + 4.0
        self.button_background_x = self.preview_panel.x + self.preview_panel.width / 2.0
        self.button_background_y = self.main_button.y - self.button_height - 1 + button_background_height / 2.0 + 1
        self.button_background_scale_x = float(self.preview_panel.width) / float(global_images.panel_frame.width)
        self.button_background_scale_y = float(button_background_height) / float(global_images.panel_frame.height)
        self.refresh_button_background_x = self.list_panel.x + self.list_panel.width / 2.0
        self.refresh_button_background_y = self.refresh_button.y - self.button_height - 1 + button_background_height / 2.0 + 1
        self.refresh_button_background_scale_x = float(self.list_panel.width) / float(global_images.panel_frame.width)
        self.refresh_button_background_scale_y = float(button_background_height) / float(global_images.panel_frame.height)
        self.playlistManager.populate_playlist()
        self.set_last_selected_row(silent=True)
        self.list_panel.on_scroll(0, silent=True)
        self.on_refresh_button_click()

    def on_stop(self):
        if self.playlistManager is not None:
            self.playlistManager.save_selected_row()
        self.list_panel.manager.dlc_manager.remove_dlc_installed_callback(self.on_dlc_installed)

    def set_last_selected_row(self, random_item = None, silent = False):
        if self.playlistManager is None:
            return
        if self.playlistManager.selected_row is not None:
            self.list_panel.select_row(self.playlistManager.selected_row, silent=silent)
        elif random_item is not None:
            self.list_panel.select_row(random_item, silent=silent)
        elif len(self.playlistManager.list_panel.rows) > 0:
            self.playlistManager.selected_row = self.list_panel.rows[0]
            self.list_panel.select_row(self.playlistManager.selected_row, silent=silent)

    def finished_getting_servers_callback(self):
        self.refresh_button.set_enabled(True)

    def got_server_callback(self, name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played):
        server = ServerInfo(name, ip, port, queryPort, ping, map, mode, num_players, max_players, tags, time_last_played)
        if not server.is_matching_version:
            return
        playlist = None
        incomplete_playlists = False
        for playlist_item in self.list_panel.rows:
            if int(playlist_item.id) == int(server.playlist_id):
                playlist = playlist_item
            elif playlist_item.ping is None or playlist_item.players is None:
                incomplete_playlists = True

        if playlist is None:
            return
        if SteamIsDemoRunning():
            if server.map in playlists.mapinfo.map_info:
                map_info = playlists.mapinfo.map_info[server.map]
                if not map_info['demo']:
                    return
            else:
                return
        if server.ping < playlist.lowest_ping:
            playlist.lowest_ping = server.ping
        playlist.server_responses.append(server)
        self.select_quick_match_server(playlist)
        if not incomplete_playlists:
            self.refresh_button.set_enabled(True)

    def select_quick_match_server(self, playlist):
        low_ping_servers = []
        populated_servers = []
        empty_servers = []
        empty_low_ping_servers = []
        low_ping = playlist.lowest_ping * 3
        for server in playlist.server_responses:
            if server.count > 0 and server.count < server.max:
                if server.ping < low_ping:
                    low_ping_servers.append(server)
                else:
                    populated_servers.append(server)
            elif server.count == 0:
                if server.ping < low_ping:
                    empty_low_ping_servers.append(server)
                else:
                    empty_servers.append(server)

        import random
        noof_empty_low_ping_servers = len(empty_low_ping_servers)
        noof_low_ping_servers = len(low_ping_servers)
        noof_populated_servers = len(populated_servers)
        noof_empty_servers = len(empty_servers)
        if noof_low_ping_servers == 0 and noof_empty_low_ping_servers == 0 and noof_populated_servers == 0 and noof_empty_servers == 0:
            return
        if noof_low_ping_servers > 0:
            index = random.randint(0, noof_low_ping_servers - 1)
            server = low_ping_servers[index]
        elif noof_empty_low_ping_servers > 0:
            index = random.randint(0, noof_empty_low_ping_servers - 1)
            server = empty_low_ping_servers[index]
        elif noof_populated_servers > 0:
            index = random.randint(0, noof_populated_servers - 1)
            server = populated_servers[index]
        else:
            index = random.randint(0, noof_empty_servers - 1)
            server = empty_servers[index]
        playlist.chosen_server = server
        playlist.ping = int(server.ping * 1000)
        playlist.players = str(server.count) + '/' + str(server.max)

    def on_row_selected(self, index, row):
        if row is None:
            return
        self.update_button_state(row)
        self.preview_panel.title = row.name
        self.preview_panel.server_type = row.server_type
        noof_modes = len(row.modes)
        if row.name == strings.RANDOM or noof_modes == 0:
            mode_id = strings.RANDOM
        elif noof_modes > 1:
            mode_id = 'multiple modes'
        elif row.modes[0] == 'cctf':
            mode_id = A2446
        else:
            mode_id = A2450[row.modes[0]]
        self.preview_panel.set_game_mode_image(mode_id)
        game_info = []
        for map in row.map_rotation:
            game_info.append(map)

        if self.playlistManager is not None:
            self.playlistManager.on_row_selected(index, row)
            self.preview_panel.set_display_data(game_info, self.playlistManager.get_selected_playlist_default_rules_as_string(), collapse_rows=True, game_info_text=strings.MAPS)

    def update_button_state(self, selected_row):
        available_playlist = selected_row.owned if hasattr(selected_row, 'owned') else True
        if available_playlist:
            self.main_button.set_enabled(True)
            self.main_button.set_visible(True)
            self.buy_now_button.set_enabled(False)
            self.buy_now_button.set_visible(False)
        else:
            self.main_button.set_enabled(False)
            self.main_button.set_visible(False)
            self.buy_now_button.set_enabled(True)
            self.buy_now_button.set_visible(True)
        self.refresh_button.set_enabled(True)
        self.refresh_button.set_visible(True)
        self.preview_panel.show_buy_button = not available_playlist

    def create_main_button(self):
        self.main_button = self.create_button(strings.START_GAME, 405, 144, 332, self.button_height, 22, self.on_main_button_click)
        self.main_button.set_enabled(False)

    def create_refresh_button(self):
        self.refresh_button = self.create_button(strings.REFRESH, 60, 144, 332, self.button_height, 22, self.on_refresh_button_click)
        self.refresh_button.set_enabled(False)

    def create_buy_button(self):
        self.buy_now_button = self.create_button(strings.BUY_NOW, 405, 144, 332, self.button_height, 22, self.on_buy_button_click)
        self.buy_now_button.set_enabled(False)
        self.buy_now_button.tint = (0.2, 1.0, 0.2)
        self.buy_now_button.text_colour = (255, 255, 255, 255)

    def on_main_button_click(self):
        selected_item = self.list_panel.get_selected_item()
        if selected_item is None or self.playlistManager is None:
            return
        from aoslib.media import HUD_AUDIO_ZONE
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if selected_item.chosen_server is not None:
            from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
            server = selected_item.chosen_server
            expected_mode = server.mode_id
            expected_classic = server.classic
            expected_skin = server.texture_skin
            self.parent.set_menu(LoadingMenu, identifier=server.identifier, server_mode=A2387, name=server.name, from_server_menu=True, expected_map=server.map, expected_mode=expected_mode, expected_classic=expected_classic, expected_skin=expected_skin, previous_menu=type(self))
        else:
            self.manager.set_menu(JoiningGameMenu, config=self.config, in_game_menu=False, server_mode=A2387, playlist_id=self.playlistManager.playlist_id, previous_menu=type(self))

    def on_refresh_button_click(self):
        steam_successful = SteamGetInternetServerList(A2387, self.got_server_callback, self.finished_getting_servers_callback)
        if steam_successful:
            self.refresh_button.set_enabled(False)
            for playlist_item in self.list_panel.rows:
                playlist_item.lowest_ping = 1000.0
                playlist_item.server_responses = []
                playlist_item.ping = None
                playlist_item.players = None
                playlist_item.chosen_server = None

    def on_buy_button_click(self):
        self.media.play('menu_buyA', zone=HUD_AUDIO_ZONE)
        if SteamIsDemoRunning():
            SteamActivateGameOverlayToStore(A0)
        else:
            SteamActivateGameOverlayToStore(DLC_APPID_LIST['mafia'])

    def open_parent_menu(self):
        from joinMatchMenu import JoinMatchMenu
        self.parent.set_menu(JoinMatchMenu, back=True)

    def on_dlc_installed(self, dlc_manager):
        self.playlistManager.populate_playlist()
        self.update_button_state(self.list_panel.get_selected_item())
        self.list_panel.on_scroll(0, silent=True)

    def draw_buttons_background(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(self.button_background_x, self.button_background_y, 0)
        gl.glScalef(self.button_background_scale_x, self.button_background_scale_y, 0.0)
        global_images.panel_frame.blit(0, 0)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(self.refresh_button_background_x, self.refresh_button_background_y, 0)
        gl.glScalef(self.refresh_button_background_scale_x, self.refresh_button_background_scale_y, 0.0)
        global_images.panel_frame.blit(0, 0)
        gl.glPopMatrix()

    def draw(self):
        super(QuickPlayMenu, self).draw()
